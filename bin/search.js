#!/usr/bin/env node
const SearchService = require('../lib/SearchService');

function parseArgs() {
  const args = process.argv.slice(2);
  let marketplace = null;
  const rest = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--marketplace') {
      marketplace = args[++i] || null;
    } else {
      rest.push(args[i]);
    }
  }
  return { marketplace, rest: rest.join(' ') };
}

async function chunkedPromiseAll(items, batchSize, fn) {
  const results = [];
  for (let i = 0; i < items.length; i += batchSize) {
    const chunk = items.slice(i, i + batchSize);
    const chunkResults = await Promise.all(chunk.map(fn));
    results.push(...chunkResults);
    if (i + batchSize < items.length) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  return results;
}

async function main() {
  const { marketplace, rest } = parseArgs();
  const cmd = rest ? rest.split(/\s+/)[0] : '';

  if (cmd === '--batch') {
    const rawList = rest.replace(/^--batch\s+/, '');
    const queries = rawList.split(',').map(q => q.trim()).filter(Boolean);
    if (!queries.length) { console.error("Usage: node bin/search.js [--marketplace cubebrush] --batch q1,q2,q3"); process.exit(1); }
    
    const results = await chunkedPromiseAll(queries, 10, async (q) => {
      try {
        const r = await SearchService.getSuggestions(q, marketplace);
        return { query: q, count: r.suggestions.length, suggestions: r.suggestions, source: r.source, marketplace: r.marketplace };
      } catch (e) {
        return { query: q, count: 0, suggestions: [], source: 'error', error: e.message, marketplace };
      }
    });
    
    console.log(JSON.stringify(results, null, 2));
    return;
  }

  const query = rest.replace(/^suggest\s+/, '').trim();
  if (!query) { console.error("Usage: node bin/search.js [--marketplace cubebrush] suggest <query>"); process.exit(1); }

  try {
    const { source, suggestions } = await SearchService.getSuggestions(query, marketplace);
    console.log(JSON.stringify(suggestions, null, 2));
    const label = marketplace ? `${marketplace}:${query}` : query;
    if (source === 'cache') {
      console.error(`[cache HIT] "${label}"`);
    } else {
      console.error(`[cache MISS] "${label}" — ${suggestions.length} suggestions`);
    }
  } catch (e) {
    console.error(e.message);
    console.log(JSON.stringify([]));
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
