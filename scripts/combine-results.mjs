import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2] ?? 'results/models';
const out = process.argv[3] ?? 'results/combined-results.json';

const files = fs.readdirSync(dir)
  .filter((name) => name.endsWith('.json') && !name.endsWith('.meta.json'))
  .sort();

const rows = [];
const sources = [];

for (const name of files) {
  const full = path.join(dir, name);
  const data = JSON.parse(fs.readFileSync(full, 'utf8'));
  const part = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];
  if (!Array.isArray(part)) continue;
  rows.push(...part);
  sources.push({ file: name, rows: part.length });
}

if (!rows.length) {
  throw new Error(`No model result rows found in ${dir}`);
}

fs.writeFileSync(out, JSON.stringify({
  combinedAt: new Date().toISOString(),
  sources,
  results: rows,
}, null, 2) + '\n');

console.log(`Combined ${rows.length} rows from ${sources.length} model result files.`);
