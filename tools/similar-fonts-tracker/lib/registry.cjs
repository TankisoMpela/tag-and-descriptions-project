const fs = require('node:fs');
const path = require('node:path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');
const REGISTRY_PATH = path.join(PROJECT_ROOT, 'outputs', 'pinterest', 'registry.json');
const PRODUCTS_PATH = path.join(__dirname, '..', 'data', 'products.json');

function similarUrl(productUrl) {
  if (!productUrl) return null;
  try {
    const url = new URL(productUrl);
    if (url.hostname !== 'creativemarket.com' && url.hostname !== 'www.creativemarket.com') return null;
    const match = url.pathname.match(/\/(\d+)-[^/]+\/?$/);
    return match ? `https://creativemarket.com/similar/fonts/${match[1]}` : null;
  } catch {
    return null;
  }
}

function sourceDetails(prepPath, fallbackName) {
  if (!prepPath) return { sourceFontName: '', sourceFontFile: '', preparedName: fallbackName };
  const nameReportPath = path.join(prepPath, 'name-report.md');
  const auditReportPath = path.join(prepPath, 'audit-report.md');
  let nameReport = '';
  let auditReport = '';
  try { nameReport = fs.readFileSync(nameReportPath, 'utf8'); } catch {}
  try { auditReport = fs.readFileSync(auditReportPath, 'utf8'); } catch {}

  const sourceFontFile = nameReport.match(/^- \*\*Source Font\*\*: (.+)$/m)?.[1]?.trim() || '';
  const preparedName = nameReport.match(/^- \*\*Final Font Name\*\*: (.+)$/m)?.[1]?.trim() || fallbackName;
  let sourceFontName = '';
  if (sourceFontFile) {
    const marker = `=== Auditing: ${sourceFontFile} ===`;
    const start = auditReport.indexOf(marker);
    if (start >= 0) {
      const rest = auditReport.slice(start + marker.length);
      const end = rest.search(/^=== Auditing: /m);
      const sourceReport = end < 0 ? rest : rest.slice(0, end);
      sourceFontName = sourceReport.match(/^\s*ID 1:\s*(.+)$/m)?.[1]?.trim() || '';
    }
    if (!sourceFontName) sourceFontName = sourceFontFile.replace(/\.[^.]+$/, '');
  }
  return { sourceFontName, sourceFontFile, preparedName };
}

function readProducts() {
  if (!fs.existsSync(REGISTRY_PATH)) return [];
  const registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  return Object.entries(registry.fonts || {}).flatMap(([slug, record]) => {
    const prepPath = record.prep_path ? path.resolve(PROJECT_ROOT, record.prep_path) : null;
    if (prepPath && !fs.existsSync(prepPath)) return [];
    const recordedUrl = record.urls?.creative_market || null;
    const relatedUrl = similarUrl(recordedUrl);
    const source = sourceDetails(prepPath, record.name || slug);
    const sourceMatch = record.source_font_match || {};
    const sourceMatchCurrent = !sourceMatch.source_name
      || sourceMatch.source_name.trim().toLocaleLowerCase() === source.sourceFontName.trim().toLocaleLowerCase();
    // A seller page or search URL is not a product. Keep the font row, but mark
    // that it still needs an exact Creative Market item link.
    const productUrl = relatedUrl ? recordedUrl : null;
    return [{
      slug,
      name: record.name || slug,
      preparedName: source.preparedName || record.name || slug,
      sourceFontName: source.sourceFontName,
      sourceFontFile: source.sourceFontFile,
      productUrl,
      similarUrl: relatedUrl,
      creativeFabricaSourceStatus: sourceMatchCurrent ? sourceMatch.status || null : null,
      creativeFabricaSourceUrl: sourceMatchCurrent && sourceMatch.status === 'found' ? sourceMatch.url || null : null,
      creativeFabricaProductUrl: record.urls?.creative_fabrica || null,
      board: record.board || null,
      number: record.number ?? null
    }];
  }).sort((a, b) => (a.number ?? Number.MAX_SAFE_INTEGER) - (b.number ?? Number.MAX_SAFE_INTEGER)
    || a.name.localeCompare(b.name) || a.slug.localeCompare(b.slug));
}

function syncProducts() {
  fs.mkdirSync(path.dirname(PRODUCTS_PATH), { recursive: true });
  const products = readProducts();
  fs.writeFileSync(PRODUCTS_PATH, `${JSON.stringify({ updatedAt: new Date().toISOString(), products }, null, 2)}\n`);
  return products;
}

module.exports = { PROJECT_ROOT, REGISTRY_PATH, PRODUCTS_PATH, similarUrl, sourceDetails, readProducts, syncProducts };
