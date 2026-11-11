const { app, BrowserWindow, ipcMain, shell } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { REGISTRY_PATH, readProducts, syncProducts } = require('./lib/registry.cjs');

const VALID_SIMILARITY = new Set(['none_found', 'found']);
const VALID_DEALT = new Set(['green', 'amber']);

function statusPath() {
  return path.join(__dirname, 'data', 'reviews.json');
}

function creativeFabricaStatusPath() {
  return path.join(__dirname, 'data', 'creative-fabrica-reviews.json');
}

function readStatuses() {
  try {
    const saved = JSON.parse(fs.readFileSync(statusPath(), 'utf8'));
    return Object.fromEntries(Object.entries(saved).map(([slug, row]) => [slug, {
      similarity: row.similarity || (['none_found', 'found'].includes(row.status) ? row.status : null),
      dealt: row.dealt || null,
      updatedAt: row.updatedAt || null
    }]));
  } catch { return {}; }
}

function readCreativeFabricaStatuses() {
  try { return JSON.parse(fs.readFileSync(creativeFabricaStatusPath(), 'utf8')); }
  catch { return {}; }
}

function validSlug(slug) {
  if (typeof slug !== 'string' || !/^[a-z0-9-]+$/.test(slug)) throw new Error('Invalid product slug.');
}

function writeSimilarity(slug, similarity) {
  validSlug(slug);
  if (similarity !== null && !VALID_SIMILARITY.has(similarity)) throw new Error('Invalid similarity mark.');
  const statuses = readStatuses();
  const current = statuses[slug] || { similarity: null, dealt: null };
  statuses[slug] = {
    similarity,
    dealt: current.similarity === similarity && similarity === 'found' ? current.dealt : null,
    updatedAt: new Date().toISOString()
  };
  fs.mkdirSync(path.dirname(statusPath()), { recursive: true });
  fs.writeFileSync(statusPath(), `${JSON.stringify(statuses, null, 2)}\n`);
  return statuses[slug];
}

function writeDealt(slug, dealt) {
  validSlug(slug);
  if (dealt !== null && !VALID_DEALT.has(dealt)) throw new Error('Invalid Dealt mark.');
  const statuses = readStatuses();
  const current = statuses[slug] || { similarity: null, dealt: null };
  if (dealt !== null && current.similarity !== 'found') {
    throw new Error('Mark a similar font found before marking Dealt.');
  }
  statuses[slug] = { ...current, dealt, updatedAt: new Date().toISOString() };
  fs.mkdirSync(path.dirname(statusPath()), { recursive: true });
  fs.writeFileSync(statusPath(), `${JSON.stringify(statuses, null, 2)}\n`);
  return statuses[slug];
}

function writeCreativeFabricaDealt(slug, dealt) {
  validSlug(slug);
  if (dealt !== null && !VALID_DEALT.has(dealt)) throw new Error('Invalid Dealt mark.');
  const product = readProducts().find(row => row.slug === slug);
  if (dealt !== null && !product?.creativeFabricaSourceUrl) {
    throw new Error('A confirmed source-font Creative Fabrica link is required before marking Dealt.');
  }
  const statuses = readCreativeFabricaStatuses();
  if (dealt === null) delete statuses[slug];
  else statuses[slug] = { dealt, updatedAt: new Date().toISOString() };
  fs.mkdirSync(path.dirname(creativeFabricaStatusPath()), { recursive: true });
  fs.writeFileSync(creativeFabricaStatusPath(), `${JSON.stringify(statuses, null, 2)}\n`);
  return statuses[slug] || { dealt: null };
}

function getSnapshot() {
  const products = syncProducts();
  const statuses = readStatuses();
  const creativeFabricaStatuses = readCreativeFabricaStatuses();
  return {
    products: products.map(product => ({
      ...product,
      similarityStatus: statuses[product.slug]?.similarity || null,
      dealtStatus: statuses[product.slug]?.dealt || null
    })),
    creativeFabrica: products.map(product => ({
      ...product,
      dealtStatus: product.creativeFabricaSourceUrl
        ? creativeFabricaStatuses[product.slug]?.dealt || null
        : null
    }))
  };
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 780,
    minWidth: 820,
    minHeight: 560,
    backgroundColor: '#111318',
    title: 'Font Review',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  ipcMain.handle('tracker:snapshot', getSnapshot);
  ipcMain.handle('tracker:set-similarity', (_event, slug, status) => writeSimilarity(slug, status));
  ipcMain.handle('tracker:set-dealt', (_event, slug, status) => writeDealt(slug, status));
  ipcMain.handle('tracker:set-cf-dealt', (_event, slug, status) => writeCreativeFabricaDealt(slug, status));
  ipcMain.handle('tracker:open-link', async (_event, rawUrl) => {
    try {
      const url = new URL(rawUrl);
      const host = url.hostname.toLowerCase();
      const allowedHost = ['creativemarket.com', 'creativefabrica.com']
        .some(domain => host === domain || host.endsWith(`.${domain}`));
      if (url.protocol !== 'https:' || !allowedHost) return false;
      await shell.openExternal(url.toString());
      return true;
    } catch { return false; }
  });
  createWindow();
  fs.watchFile(REGISTRY_PATH, { interval: 700 }, () => {
    syncProducts();
    for (const win of BrowserWindow.getAllWindows()) win.webContents.send('tracker:products-updated');
  });
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
