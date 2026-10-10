#!/usr/bin/env node

/**
 * Compile one already-authored OpenPencil JSX composition into a .fig file.
 *
 * This helper intentionally has no layout vocabulary of its own. It is a
 * mechanical entry point for the agent's one-image JSX source, so the source
 * remains the design and the resulting .fig remains inspectable in
 * OpenPencil. Use render_openpencil_font_handoff.mjs for the font-aware PNG.
 */

import { readFile, stat, writeFile } from 'node:fs/promises'
import { basename, dirname, join, resolve } from 'node:path'

import { BUILTIN_IO_FORMATS, IORegistry } from '@open-pencil/core/io'
import { renderJSX } from '@open-pencil/core/design-jsx'
import { SceneGraph } from '@open-pencil/scene-graph'

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

function required(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} must be a non-empty string`)
  return value
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const source = resolve(required(args.source, '--source'))
  const output = resolve(required(args.output, '--output'))
  try {
    await stat(output)
    throw new Error(`refusing to overwrite existing OpenPencil document: ${output}`)
  } catch (error) {
    if (error.code !== 'ENOENT') throw error
  }

  const graph = new SceneGraph()
  const page = graph.addPage(args.page || basename(source, '.jsx'))
  const jsx = await readFile(source, 'utf8')
  const created = await renderJSX(graph, jsx, { parentId: page.id })
  if (!created.length) throw new Error(`OpenPencil JSX created no root node: ${source}`)

  const io = new IORegistry(BUILTIN_IO_FORMATS)
  const result = await io.writeDocument('fig', graph)
  await writeFile(output, result.data)
  const reportPath = join(dirname(output), `${basename(output, '.fig')}.compile-report.json`)
  await writeFile(reportPath, JSON.stringify({
    source,
    output,
    page: page.name,
    roots: created.map((node) => ({ id: node.id, name: node.name, type: node.type, width: node.width, height: node.height })),
    note: 'Compilation preserved the authored JSX; no template, copy, palette, or layout was applied by this helper.'
  }, null, 2) + '\n')
  console.log(JSON.stringify({ output, source, roots: created.map((node) => node.name) }, null, 2))
}

main().catch((error) => {
  console.error(`[FAIL] ${error.message}`)
  process.exitCode = 1
})
