#!/usr/bin/env node

/**
 * Render an Agent-27 OpenPencil handoff with the supplied local fonts.
 *
 * This is deliberately a bridge, not a design generator. It never selects a
 * layout, changes a node, replaces copy, or applies a palette. The plan
 * points at already-authored .fig files; this command loads those files,
 * registers the real font bytes with OpenPencil's headless renderer, exports
 * the named root frame, and writes a structural render report.
 */

import { copyFile, mkdir, readFile, stat, writeFile } from 'node:fs/promises'
import { basename, dirname, extname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  BUILTIN_IO_FORMATS,
  IORegistry,
  headlessRenderNodes,
  initCanvasKit
} from '@open-pencil/core/io'
import { fontManager } from '@open-pencil/core/text'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const workspaceRoot = resolve(scriptDir, '..')

function parseArgs(argv) {
  const args = {}
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('--')) throw new Error(`unexpected argument: ${token}`)
    const key = token.slice(2)
    const value = argv[index + 1]
    if (!value || value.startsWith('--')) throw new Error(`missing value for --${key}`)
    args[key] = value
    index += 1
  }
  return args
}

function requiredString(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} must be a non-empty string`)
  return value
}

function resolvePlanPath(value, planPath) {
  const candidate = resolve(dirname(planPath), value)
  return candidate
}

function toArrayBuffer(data) {
  return data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength)
}

async function registerFonts(plan, planPath) {
  const entries = []
  if (Array.isArray(plan.font_files)) entries.push(...plan.font_files)
  if (Array.isArray(plan.auxiliary_font_files)) entries.push(...plan.auxiliary_font_files)
  if (typeof plan.primary_font === 'string' && plan.primary_font.trim()) {
    entries.push({
      family: plan.font_name,
      style: 'Regular',
      path: plan.primary_font
    })
  }

  const seen = new Set()
  for (const [index, entry] of entries.entries()) {
    if (!entry || typeof entry !== 'object') throw new Error(`font_files[${index}] must be an object`)
    const family = requiredString(entry.family, `font_files[${index}].family`)
    const style = typeof entry.style === 'string' && entry.style.trim() ? entry.style : 'Regular'
    const path = resolvePlanPath(requiredString(entry.path, `font_files[${index}].path`), planPath)
    const key = `${family}\0${style}\0${path}`
    if (seen.has(key)) continue
    seen.add(key)
    const data = await readFile(path)
    fontManager.markLoaded(family, style, toArrayBuffer(data))
  }
  if (!seen.size) throw new Error('visual plan requires font_files or primary_font for local-font rendering')
  return [...seen].map((key) => key.split('\0').slice(0, 2).join(' / '))
}

async function loadFig(source) {
  const io = new IORegistry(BUILTIN_IO_FORMATS)
  const data = new Uint8Array(await readFile(source))
  const result = await io.readDocument({ name: basename(source), data })
  return result.graph
}

function pageForRoot(graph, rootName, pageName) {
  const pages = graph.getPages(true)
  const namedPage = typeof pageName === 'string' && pageName.trim()
    ? pages.find((page) => page.name === pageName)
    : null
  const pagesToSearch = namedPage ? [namedPage] : pages
  if (namedPage === null && pageName) throw new Error(`OpenPencil page not found: ${pageName}`)

  for (const page of pagesToSearch) {
    const match = graph.getChildren(page.id).find((node) => node.name === rootName)
    if (match) return { page, root: match }
  }
  const fallback = [...graph.getAllNodes()].find((node) => node.name === rootName)
  if (fallback) {
    const page = pages.find((candidate) => graph.isDescendant(fallback.id, candidate.id))
    if (page) return { page, root: fallback }
  }
  throw new Error(`OpenPencil root frame not found: ${rootName}`)
}

function descendantNodes(graph, root) {
  return [...graph.getAllNodes()].filter((node) => node.id === root.id || graph.isDescendant(node.id, root.id))
}

function textReport(graph, root) {
  return descendantNodes(graph, root)
    .filter((node) => node.type === 'TEXT')
    .map((node) => ({
      id: node.id,
      name: node.name,
      text: node.text,
      fontFamily: node.fontFamily,
      fontSize: node.fontSize,
      x: node.x,
      y: node.y,
      width: node.width,
      height: node.height
    }))
}

function copyCheck(copyBlocks, textNodes) {
  const allText = textNodes.map((node) => node.text || '').join('\n')
  const blocks = Array.isArray(copyBlocks) ? copyBlocks.filter((value) => typeof value === 'string' && value.trim()) : []
  return {
    requested: blocks,
    present: blocks.filter((block) => allText.includes(block)),
    missing: blocks.filter((block) => !allText.includes(block))
  }
}

function expectedFeaturedFamilies(plan, asset) {
  const planFamilies = Array.isArray(plan.featured_font_families)
    ? plan.featured_font_families
    : []
  const assetFamilies = Array.isArray(asset?.featured_font_families)
    ? asset.featured_font_families
    : []
  const fontFileFamilies = Array.isArray(plan.font_files)
    ? plan.font_files.map((entry) => entry?.family)
    : []
  const candidates = [...assetFamilies, ...planFamilies, ...fontFileFamilies]
  return [...new Set(candidates.filter((value) => typeof value === 'string' && value.trim()).map((value) => value.trim()))]
}

async function renderAsset({ plan, planPath, output, asset, assetName, ratio, dimensions, registeredFonts }) {
  const sourceFiles = asset?.source_files
  const sourceValue = sourceFiles && sourceFiles[ratio]
  const source = resolvePlanPath(requiredString(sourceValue, `${assetName}.source_files.${ratio}`), planPath)
  if (extname(source).toLowerCase() !== '.fig') throw new Error(`${assetName} ${ratio} source must be an OpenPencil .fig file: ${source}`)

  const graph = await loadFig(source)
  const rootName = asset.root_names && typeof asset.root_names[ratio] === 'string' && asset.root_names[ratio].trim()
    ? asset.root_names[ratio]
    : typeof asset.root_name === 'string' && asset.root_name.trim()
    ? asset.root_name
    : typeof plan.root_name === 'string' && plan.root_name.trim()
      ? plan.root_name
      : basename(source, '.fig')
  const { page, root } = pageForRoot(graph, rootName, asset.page_name || plan.page_name)
  const expectedWidth = dimensions[0]
  const expectedHeight = dimensions[1]
  if (Math.round(root.width) !== expectedWidth || Math.round(root.height) !== expectedHeight) {
    throw new Error(`${assetName} ${ratio} root is ${root.width}x${root.height}; expected ${expectedWidth}x${expectedHeight}`)
  }

  const texts = textReport(graph, root)
  const plannedCopy = asset.copy_blocks_by_ratio?.[ratio] || asset.copy_blocks
  const copies = copyCheck(plannedCopy, texts)
  if (copies.missing.length) {
    throw new Error(`${assetName} ${ratio} is missing planned copy blocks: ${copies.missing.join(' | ')}`)
  }
  const featuredFamilies = expectedFeaturedFamilies(plan, asset)
  if (!featuredFamilies.length) {
    throw new Error(`${assetName} ${ratio} requires featured_font_families or product font_files families`)
  }
  const actualFamilies = [...new Set(texts.map((node) => node.fontFamily).filter(Boolean))]
  const featuredPresent = featuredFamilies.some((family) => actualFamilies.includes(family))
  if (!featuredPresent) {
    throw new Error(`${assetName} ${ratio} does not contain the expected product font family. Expected one of: ${featuredFamilies.join(', ')}. Found: ${actualFamilies.join(', ') || 'none'}`)
  }
  const png = await headlessRenderNodes(graph, page.id, [root.id], { format: 'PNG', scale: 1 })
  if (!png) throw new Error(`OpenPencil produced no PNG for ${assetName} ${ratio}`)

  const outputName = assetName === 'thumbnail_main' ? 'thumbnail_main' : assetName
  const pngPath = join(output, ratio, `${outputName}.png`)
  const sourcePath = join(output, 'openpencil', ratio, `${outputName}.fig`)
  await mkdir(dirname(pngPath), { recursive: true })
  await mkdir(dirname(sourcePath), { recursive: true })
  await writeFile(pngPath, png)
  await copyFile(source, sourcePath)

  const jsxSource = source.replace(/\.fig$/i, '.jsx')
  let jsxPath = null
  try {
    await readFile(jsxSource)
    jsxPath = join(output, 'openpencil', ratio, `${outputName}.jsx`)
    await copyFile(jsxSource, jsxPath)
  } catch (error) {
    if (error.code !== 'ENOENT') throw error
  }

  return {
    asset: assetName,
    ratio,
    source: relative(output, sourcePath),
    jsx: jsxPath ? relative(output, jsxPath) : null,
    output: relative(output, pngPath),
    page: page.name,
    root: { id: root.id, name: root.name, width: root.width, height: root.height },
    nodeCount: descendantNodes(graph, root).length,
    textNodes: texts,
    fontFamilies: actualFamilies,
    featuredFontFamilies: featuredFamilies,
    copy: copies,
    registeredFonts,
    checks: {
      exactCanvasDimensions: true,
      plannedCopyPresent: true,
      featuredFontPresent: true,
      localFontsRegistered: true,
      renderedWithOpenPencilCore: true
    }
  }
}

function assetsFromPlan(plan) {
  if (!plan.thumbnail || typeof plan.thumbnail !== 'object') throw new Error('visual plan requires thumbnail')
  if (!Array.isArray(plan.promos) || plan.promos.length < 4 || plan.promos.length > 8) throw new Error('visual plan requires 4-8 supporting promos')
  const assets = [{ name: 'thumbnail_main', value: plan.thumbnail }]
  plan.promos.forEach((promo, index) => assets.push({ name: `promo_${index + 1}`, value: promo }))
  if (!plan.japanese_thumbnail || typeof plan.japanese_thumbnail !== 'object') throw new Error('visual plan requires japanese_thumbnail')
  assets.push({ name: 'thumbnail_japanese', value: plan.japanese_thumbnail, ratios: ['1x1'] })
  return assets
}

async function renderPlan(planPath, output) {
  const plan = JSON.parse(await readFile(planPath, 'utf8'))
  if (!plan || typeof plan !== 'object') throw new Error('visual plan root must be an object')
  if (!['openpencil', 'open-pencil'].includes(plan.render_mode)) throw new Error('OpenPencil handoff requires render_mode=openpencil')
  if (output.exists) throw new Error(`refusing to overwrite existing visual handoff: ${output.path}`)

  const dimensions = plan.dimensions || { '3x2': [2400, 1600], '1x1': [1600, 1600] }
  const registeredFonts = await registerFonts(plan, planPath)
  await initCanvasKit()
  const reports = []
  for (const asset of assetsFromPlan(plan)) {
    const ratios = asset.ratios || ['3x2', '1x1']
    for (const ratio of ratios) {
      if (!Array.isArray(dimensions[ratio]) || dimensions[ratio].length !== 2) throw new Error(`missing dimensions for ${ratio}`)
      reports.push(await renderAsset({
        plan,
        planPath,
        output: output.path,
        asset: asset.value,
        assetName: asset.name,
        ratio,
        dimensions: dimensions[ratio],
        registeredFonts
      }))
    }
  }
  await writeFile(join(output.path, 'openpencil-render-report.json'), JSON.stringify({
    renderer: '@open-pencil/core',
    rendererVersion: '0.14.0',
    workspaceRoot,
    plan: planPath,
    reports
  }, null, 2) + '\n')
  return reports
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const planValue = requiredString(args.plan, '--plan')
  const outputValue = requiredString(args.output, '--output')
  const planPath = resolve(planValue)
  const output = { path: resolve(outputValue), exists: false }
  try {
    await stat(output.path)
    output.exists = true
  } catch (error) {
    if (error.code !== 'ENOENT') throw error
  }
  const reports = await renderPlan(planPath, output)
  console.log(JSON.stringify({ output: output.path, rendered: reports.length }, null, 2))
}

main().catch((error) => {
  console.error(`[FAIL] ${error.message}`)
  process.exitCode = 1
})
