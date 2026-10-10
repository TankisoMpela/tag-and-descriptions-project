'use strict';

const https = require('https');
const cache = require('./CacheRepository');

const agent = new https.Agent({
  keepAlive: true,
  maxSockets: 20,
  keepAliveMsecs: 10000
});

class SearchService {
  static async getSuggestions(query, marketplace) {
    if (!query) {
      throw new Error("Query is required");
    }

    const searchQuery = marketplace ? `${marketplace} ${query}` : query;
    const sourceKey = marketplace ? `curl:${marketplace}` : 'curl';

    const cached = await cache.getCachedSearch(searchQuery, sourceKey);
    if (cached !== null) {
      return { source: 'cache', suggestions: cached, marketplace };
    }

    const url = `https://suggestqueries.google.com/complete/search?client=firefox&q=${encodeURIComponent(searchQuery)}`;

    try {
      const raw = await new Promise((resolve, reject) => {
        https.get(url, { agent, timeout: 10000 }, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => resolve(data));
        }).on('error', reject).on('timeout', function() { this.destroy(); reject(new Error('Request timed out')); });
      });

      let suggestions = [];
      try {
        const parsed = JSON.parse(raw);
        suggestions = parsed[1] || [];
      } catch { suggestions = []; }

      await cache.cacheSearch(searchQuery, suggestions, sourceKey);
      return { source: 'network', suggestions, marketplace };
    } catch (e) {
      throw new Error(`suggestqueries failed: ${e.message}`);
    }
  }
}

module.exports = SearchService;
