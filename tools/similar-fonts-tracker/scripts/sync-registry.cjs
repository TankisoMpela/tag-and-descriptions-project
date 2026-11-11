const { syncProducts } = require('../lib/registry.cjs');

const products = syncProducts();
const linked = products.filter(product => product.productUrl).length;
console.log(`Tracker refreshed: ${products.length} font rows (${linked} with a Creative Market link, ${products.length - linked} marked No CM link yet).`);
