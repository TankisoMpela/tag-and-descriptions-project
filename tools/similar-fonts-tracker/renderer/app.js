const table = document.querySelector('#font-table');
const columns = document.querySelector('#columns');
const body = document.querySelector('#rows');
const tabs = [...document.querySelectorAll('[data-sheet]')];
const previousPage = document.querySelector('#previous-page');
const nextPage = document.querySelector('#next-page');
const pageInfo = document.querySelector('#page-info');
const pageSize = 10;
const viewStateKey = 'similar-fonts-tracker:view-state:v1';

function readViewState() {
  try {
    const saved = JSON.parse(localStorage.getItem(viewStateKey) || '{}');
    const safePage = value => Number.isInteger(value) && value >= 0 ? value : 0;
    const safeSlugs = value => Array.isArray(value)
      ? value.filter(slug => typeof slug === 'string')
      : [];
    return {
      activeSheet: saved.activeSheet === 'fabrica' ? 'fabrica' : 'market',
      pages: {
        market: safePage(saved.pages?.market),
        fabrica: safePage(saved.pages?.fabrica)
      },
      anchors: {
        market: typeof saved.anchors?.market === 'string' ? saved.anchors.market : null,
        fabrica: typeof saved.anchors?.fabrica === 'string' ? saved.anchors.fabrica : null
      },
      order: {
        market: safeSlugs(saved.order?.market),
        fabrica: safeSlugs(saved.order?.fabrica)
      }
    };
  } catch {
    return {
      activeSheet: 'market',
      pages: { market: 0, fabrica: 0 },
      anchors: { market: null, fabrica: null },
      order: { market: [], fabrica: [] }
    };
  }
}

const viewState = readViewState();
let marketProducts = [];
let fabricaProducts = [];
let activeSheet = viewState.activeSheet;
let page = viewState.pages[activeSheet];
let loadRequest = 0;

function saveViewState() {
  viewState.activeSheet = activeSheet;
  viewState.pages[activeSheet] = page;
  try { localStorage.setItem(viewStateKey, JSON.stringify(viewState)); } catch {}
}

function keepProductOrder(products, sheet) {
  const savedOrder = viewState.order[sheet];
  if (savedOrder.length === 0) {
    viewState.order[sheet] = products.map(product => product.slug);
    return products;
  }

  const position = new Map(savedOrder.map((slug, index) => [slug, index]));
  const ordered = [...products].sort((left, right) => {
    const leftPosition = position.get(left.slug);
    const rightPosition = position.get(right.slug);
    if (leftPosition !== undefined && rightPosition !== undefined) return leftPosition - rightPosition;
    if (leftPosition !== undefined) return -1;
    if (rightPosition !== undefined) return 1;
    return 0;
  });
  viewState.order[sheet] = ordered.map(product => product.slug);
  return ordered;
}

function addLink(cell, url) {
  if (!url) return;
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.textContent = url;
  anchor.title = url;
  anchor.addEventListener('click', event => {
    event.preventDefault();
    saveViewState();
    window.tracker.openLink(url);
  });
  cell.append(anchor);
}

function addMarks(cell, product, options, selected, setStatus, labelBase, applySaved) {
  cell.className = 'marks';
  for (const [value, color, label] of options) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `mark ${color}${selected === value ? ' selected' : ''}`;
    button.title = label;
    button.setAttribute('aria-label', `${label}: ${labelBase}`);
    button.setAttribute('aria-pressed', String(selected === value));
    button.addEventListener('click', async () => {
      const next = selected === value ? null : value;
      button.disabled = true;
      try {
        const saved = await setStatus(product.slug, next);
        applySaved(saved);
        render();
      } finally {
        button.disabled = false;
      }
    });
    cell.append(button);
  }
}

function appendTextCell(row, value) {
  const cell = document.createElement('td');
  cell.textContent = value || '';
  row.append(cell);
  return cell;
}

function marketRow(product) {
  const row = document.createElement('tr');
  appendTextCell(row, product.preparedName || product.name);
  appendTextCell(row, product.sourceFontName || product.sourceFontFile);

  const productLink = document.createElement('td');
  if (product.productUrl) addLink(productLink, product.productUrl);
  else productLink.textContent = 'No CM link yet';
  row.append(productLink);

  const similarLink = document.createElement('td');
  addLink(similarLink, product.similarUrl);
  row.append(similarLink);

  const similarity = document.createElement('td');
  addMarks(similarity, product, [
    ['none_found', 'green', 'No similar font found'],
    ['found', 'red', 'Similar font found']
  ], product.similarityStatus, window.tracker.setSimilarity, product.name, saved => {
    product.similarityStatus = saved.similarity;
    product.dealtStatus = saved.dealt;
  });
  row.append(similarity);

  const dealt = document.createElement('td');
  if (product.similarityStatus === 'found') {
    addMarks(dealt, product, [
      ['green', 'green', 'Dealt green'],
      ['amber', 'amber', 'Dealt amber']
    ], product.dealtStatus, window.tracker.setDealt, product.name, saved => {
      product.dealtStatus = saved.dealt;
    });
  } else dealt.className = 'marks';
  row.append(dealt);
  return row;
}

function fabricaRow(product) {
  const row = document.createElement('tr');
  appendTextCell(row, product.sourceFontName || product.sourceFontFile);
  appendTextCell(row, product.preparedName || product.name);

  const sourceMatch = document.createElement('td');
  if (product.creativeFabricaSourceUrl) addLink(sourceMatch, product.creativeFabricaSourceUrl);
  else if (product.creativeFabricaSourceStatus === 'not_found') sourceMatch.textContent = 'No match found';
  else sourceMatch.textContent = 'Not searched';
  row.append(sourceMatch);

  const preparedListing = document.createElement('td');
  addLink(preparedListing, product.creativeFabricaProductUrl);
  if (!product.creativeFabricaProductUrl) preparedListing.textContent = 'No CF link yet';
  row.append(preparedListing);

  const dealt = document.createElement('td');
  dealt.className = 'marks';
  if (product.creativeFabricaSourceUrl) {
    addMarks(dealt, product, [
      ['green', 'green', 'Dealt green'],
      ['amber', 'amber', 'Dealt amber']
    ], product.dealtStatus, window.tracker.setCreativeFabricaDealt, product.sourceFontName || product.sourceFontFile, saved => {
      product.dealtStatus = saved.dealt;
    });
  }
  row.append(dealt);
  return row;
}

function render() {
  const products = activeSheet === 'market' ? marketProducts : fabricaProducts;
  const pageCount = Math.ceil(products.length / pageSize);
  const anchorSlug = viewState.anchors[activeSheet];
  if (anchorSlug) {
    const anchorIndex = products.findIndex(product => product.slug === anchorSlug);
    if (anchorIndex >= 0) page = Math.floor(anchorIndex / pageSize);
    else viewState.anchors[activeSheet] = null;
  }
  page = Math.min(page, Math.max(0, pageCount - 1));
  const start = page * pageSize;
  const visible = products.slice(start, start + pageSize);

  for (const tab of tabs) {
    const selected = tab.dataset.sheet === activeSheet;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  }

  table.dataset.sheet = activeSheet;
  columns.replaceChildren();
  const headings = activeSheet === 'market'
    ? ['Prepared name', 'Source name', 'Creative Market', 'Similar Fonts', 'Similar', 'Dealt']
    : ['Source font', 'Prepared name', 'Source on Creative Fabrica', 'Prepared listing', 'Dealt'];
  for (const heading of headings) {
    const th = document.createElement('th');
    th.scope = 'col';
    th.textContent = heading;
    columns.append(th);
  }

  body.replaceChildren(...visible.map(activeSheet === 'market' ? marketRow : fabricaRow));
  if (visible.length) viewState.anchors[activeSheet] = visible[0].slug;
  const first = products.length ? start + 1 : 0;
  const last = Math.min(start + visible.length, products.length);
  pageInfo.textContent = `${first}–${last} of ${products.length}`;
  previousPage.disabled = page === 0;
  nextPage.disabled = page >= pageCount - 1;
  saveViewState();
}

async function loadProducts() {
  const request = ++loadRequest;
  const snapshot = await window.tracker.snapshot();
  if (request !== loadRequest) return;
  marketProducts = keepProductOrder(snapshot.products || [], 'market');
  fabricaProducts = keepProductOrder(snapshot.creativeFabrica || [], 'fabrica');
  render();
}

for (const tab of tabs) {
  tab.addEventListener('click', () => {
    viewState.pages[activeSheet] = page;
    activeSheet = tab.dataset.sheet;
    page = viewState.pages[activeSheet];
    render();
  });
}
previousPage.addEventListener('click', () => {
  if (page > 0) {
    page -= 1;
    viewState.anchors[activeSheet] = null;
    render();
  }
});
nextPage.addEventListener('click', () => {
  const products = activeSheet === 'market' ? marketProducts : fabricaProducts;
  if ((page + 1) * pageSize < products.length) {
    page += 1;
    viewState.anchors[activeSheet] = null;
    render();
  }
});

loadProducts();
window.tracker.onProductsUpdated(loadProducts);
