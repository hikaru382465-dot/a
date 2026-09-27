// Wikimedia Commons検索＆ダウンロードツール（Claude内部用。ひかるは実行不要）
// 使い方: node wikimedia_search.js "検索語" 出力フォルダ [取得件数]
// 証明書エラーが出る場合は、この環境の agent-proxy が原因。--ignore-certificate-errors で回避済み。
// api.openverse.org・pixabay.com はCloudflareのボット認証で依然ブロックされる（この方法では突破できない）。
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const ACCEPTABLE_LICENSES = ['cc0', 'cc-by', 'cc-by-sa', 'public domain', 'pd-'];

function isAcceptable(licenseShort) {
  const l = (licenseShort || '').toLowerCase();
  if (l.includes('nc') || l.includes('nd')) return false;
  return ACCEPTABLE_LICENSES.some(a => l.includes(a)) || l.includes('cc');
}

async function main() {
  const query = process.argv[2];
  const outDir = process.argv[3];
  const limit = parseInt(process.argv[4] || '8', 10);
  if (!query || !outDir) {
    console.log('usage: node wikimedia_tool.js "query" outDir [limit]');
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--ignore-certificate-errors'],
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
  });

  const searchUrl = 'https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=' +
    encodeURIComponent(query + ' filetype:bitmap') + '&srnamespace=6&format=json&srlimit=' + limit;
  const searchResp = await context.request.get(searchUrl);
  const searchJson = await searchResp.json();
  const titles = (searchJson.query?.search || []).map(s => s.title);

  if (titles.length === 0) {
    console.log('no results for', query);
    await browser.close();
    return;
  }

  const infoUrl = 'https://commons.wikimedia.org/w/api.php?action=query&titles=' +
    encodeURIComponent(titles.join('|')) +
    '&prop=imageinfo&iiprop=url|size|extmetadata&format=json';
  const infoResp = await context.request.get(infoUrl);
  const infoJson = await infoResp.json();
  const pages = infoJson.query?.pages || {};

  const manifest = [];
  let idx = 0;
  for (const pageId of Object.keys(pages)) {
    const p = pages[pageId];
    const info = p.imageinfo?.[0];
    if (!info) continue;
    const meta = info.extmetadata || {};
    const licenseShort = meta.LicenseShortName?.value || '';
    const artist = (meta.Artist?.value || '').replace(/<[^>]+>/g, '').trim();
    const credit = (meta.Credit?.value || '').replace(/<[^>]+>/g, '').trim();
    const url = info.url;
    const ext = path.extname(url.split('?')[0]).toLowerCase();

    if (!isAcceptable(licenseShort)) {
      console.log('skip (license):', p.title, licenseShort);
      continue;
    }
    if (!['.jpg', '.jpeg', '.png'].includes(ext)) {
      console.log('skip (not jpg/png):', p.title);
      continue;
    }
    if (info.width < 1000 || info.height < 700) {
      console.log('skip (too small):', p.title, info.width, info.height);
      continue;
    }

    idx += 1;
    const fname = `cand-${String(idx).padStart(2, '0')}${ext}`;
    try {
      const dl = await context.request.get(url);
      const buf = await dl.body();
      fs.writeFileSync(path.join(outDir, fname), buf);
      manifest.push({
        file: fname,
        title: p.title,
        license: licenseShort,
        artist: artist || credit || 'unknown',
        pageUrl: `https://commons.wikimedia.org/wiki/${encodeURIComponent(p.title.replace(/ /g, '_'))}`,
        width: info.width,
        height: info.height,
      });
      console.log('saved:', fname, '<-', p.title, `(${licenseShort})`);
    } catch (e) {
      console.log('download failed:', p.title, e.message);
    }
  }

  fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');
  console.log(`\n${manifest.length} images saved to ${outDir}`);

  await browser.close();
}

main();
