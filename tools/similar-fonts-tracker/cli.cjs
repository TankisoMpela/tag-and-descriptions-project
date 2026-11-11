#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const { readProducts } = require('./lib/registry.cjs');

const reviewPath = path.join(__dirname, 'data', 'reviews.json');
const cfReviewPath = path.join(__dirname, 'data', 'creative-fabrica-reviews.json');
const command = process.argv[2] || 'summary';
let reviews = {};
let cfReviews = {};
try { reviews = JSON.parse(fs.readFileSync(reviewPath, 'utf8')); } catch {}
try { cfReviews = JSON.parse(fs.readFileSync(cfReviewPath, 'utf8')); } catch {}

const products = readProducts().map(product => {
  const saved = reviews[product.slug] || {};
  return {
    ...product,
    similarityStatus: saved.similarity || (['none_found', 'found'].includes(saved.status) ? saved.status : null),
    dealtStatus: saved.dealt || null
  };
});
const cfProducts = readProducts().map(product => ({
  ...product,
  dealtStatus: product.creativeFabricaSourceUrl ? cfReviews[product.slug]?.dealt || null : null
}));

if (command === 'summary') {
  const counts = {
    products: products.length,
    missing_cm_link: products.filter(product => !product.productUrl).length,
    similarity_unreviewed: products.filter(product => !product.similarityStatus).length,
    none_found: products.filter(product => product.similarityStatus === 'none_found').length,
    similar_found: products.filter(product => product.similarityStatus === 'found').length,
    dealt_pending: products.filter(product => product.similarityStatus === 'found' && !product.dealtStatus).length,
    dealt_green: products.filter(product => product.similarityStatus === 'found' && product.dealtStatus === 'green').length,
    dealt_amber: products.filter(product => product.similarityStatus === 'found' && product.dealtStatus === 'amber').length
  };
  console.log(JSON.stringify(counts, null, 2));
} else if (command === 'list') {
  console.log(JSON.stringify(products, null, 2));
} else if (command === 'show') {
  const product = products.find(row => row.slug === process.argv[3]);
  if (!product) {
    console.error(`No catalog font found for slug: ${process.argv[3] || '(missing)'}`);
    process.exitCode = 1;
  } else console.log(JSON.stringify(product, null, 2));
} else if (command === 'cf-summary') {
  console.log(JSON.stringify({
    products: cfProducts.length,
    source_matches_found: cfProducts.filter(product => product.creativeFabricaSourceUrl).length,
    source_match_not_found: cfProducts.filter(product => product.creativeFabricaSourceStatus === 'not_found').length,
    source_match_unchecked: cfProducts.filter(product => !product.creativeFabricaSourceStatus).length,
    dealt_pending: cfProducts.filter(product => product.creativeFabricaSourceUrl && !product.dealtStatus).length,
    dealt_green: cfProducts.filter(product => product.dealtStatus === 'green').length,
    dealt_amber: cfProducts.filter(product => product.dealtStatus === 'amber').length
  }, null, 2));
} else if (command === 'cf-list') {
  console.log(JSON.stringify(cfProducts, null, 2));
} else if (command === 'cf-show') {
  const product = cfProducts.find(row => row.slug === process.argv[3]);
  if (!product) {
    console.error(`No catalog font found for slug: ${process.argv[3] || '(missing)'}`);
    process.exitCode = 1;
  } else console.log(JSON.stringify(product, null, 2));
} else if (command === 'set-cf-dealt') {
  const [, , , slug, value] = process.argv;
  const product = cfProducts.find(row => row.slug === slug);
  if (!product) {
    console.error(`No catalog font found for slug: ${slug || '(missing)'}`);
    process.exitCode = 1;
  } else if (!product.creativeFabricaSourceUrl && value !== 'clear') {
    console.error('A confirmed source-font Creative Fabrica link is required before marking Dealt.');
    process.exitCode = 1;
  } else if (!['green', 'amber', 'clear'].includes(value)) {
    console.error('Use: node cli.cjs set-cf-dealt <slug> <green|amber|clear>');
    process.exitCode = 2;
  } else {
    if (value === 'clear') delete cfReviews[slug];
    else cfReviews[slug] = { dealt: value, updatedAt: new Date().toISOString() };
    fs.mkdirSync(path.dirname(cfReviewPath), { recursive: true });
    fs.writeFileSync(cfReviewPath, `${JSON.stringify(cfReviews, null, 2)}\n`);
    console.log(`${slug}: Creative Fabrica Dealt ${value}`);
  }
} else {
  console.error('Usage: node cli.cjs [summary|list|show <slug>|cf-summary|cf-list|cf-show <slug>|set-cf-dealt <slug> <green|amber|clear>]');
  process.exitCode = 2;
}
