#!/usr/bin/env node
// お客さんのサイトを納品前にチェックする。
// 使い方: node .claude/skills/client-site/scripts/check_site.cjs works/<slug>
// FAIL が1つでもあれば終了コード1で終わる。

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function loadPlaywright() {
  try {
    return require('playwright');
  } catch {
    const globalRoot = execSync('npm root -g').toString().trim();
    return require(path.join(globalRoot, 'playwright'));
  }
}

const siteDir = process.argv[2];
if (!siteDir) {
  console.error('使い方: node check_site.cjs works/<slug>');
  process.exit(2);
}
const indexPath = path.resolve(siteDir, 'index.html');
if (!fs.existsSync(indexPath)) {
  console.error(`見つかりません: ${indexPath}`);
  process.exit(2);
}

const slug = path.basename(path.resolve(siteDir));
const outDir = path.resolve('.check', slug);
fs.mkdirSync(outDir, { recursive: true });

const VIEWPORTS = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'pc', width: 1280, height: 800 },
];

// 本物のお客さんのサイトに残っていてはいけない仮置きの文字
const PLACEHOLDERS = [
  { re: /【要確認[^】]*】/g, label: '【要確認】の仮置き' },
  { re: /【(?!要確認)[^】]{1,30}】/g, label: '【 】で囲まれた仮置き' },
  { re: /○○/g, label: '○○' },
  { re: /000-0000/g, label: '000-0000（仮の電話番号）' },
  { re: /サンプル/g, label: '「サンプル」という文字' },
  { re: /\[あなたの名前\]/g, label: '[あなたの名前]' },
  { re: /lorem ipsum/gi, label: 'lorem ipsum' },
];

const results = [];
const add = (level, msg) => results.push({ level, msg });

(async () => {
  const { chromium } = loadPlaywright();
  const launchOpts = {};
  if (fs.existsSync('/opt/pw-browsers/chromium')) launchOpts.executablePath = '/opt/pw-browsers/chromium';
  const browser = await chromium.launch(launchOpts);

  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } });
    // 外部の画像やフォントが読み込めない環境でも、チェック自体は止めない
    await page.goto('file://' + indexPath, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    if (scrollWidth > vp.width) {
      const culprits = await page.evaluate((w) =>
        [...document.querySelectorAll('body *')]
          .filter((el) => el.getBoundingClientRect().right > w + 1)
          .slice(0, 5)
          .map((el) => el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '')),
        vp.width);
      add('FAIL', `${vp.name}（幅${vp.width}px）で横にはみ出しています（${scrollWidth}px）。はみ出している要素: ${culprits.join(', ')}`);
    } else {
      add('OK', `${vp.name}（幅${vp.width}px）で横のはみ出しなし`);
    }

    const shot = path.join(outDir, `${vp.name}.png`);
    await page.screenshot({ path: shot, fullPage: true });
    add('INFO', `画面の画像を保存: ${path.relative(process.cwd(), shot)}`);

    if (vp.name === 'mobile') {
      const info = await page.evaluate(() => {
        const text = document.body.innerText;
        const imgs = [...document.images].map((img) => ({
          src: img.getAttribute('src') || '',
          alt: img.getAttribute('alt'),
        }));
        const telLinks = [...document.querySelectorAll('a[href^="tel:"]')].length;
        const phoneLike = (text.match(/0\d{1,4}-\d{1,4}-\d{3,4}/g) || []).length;
        return {
          text,
          imgs,
          telLinks,
          phoneLike,
          title: document.title,
          description: document.querySelector('meta[name="description"]')?.content || '',
          noindex: !!document.querySelector('meta[name="robots"][content*="noindex"]'),
          sampleBar: !!document.querySelector('.sample-bar'),
          viewportMeta: !!document.querySelector('meta[name="viewport"]'),
        };
      });

      for (const p of PLACEHOLDERS) {
        const hits = info.text.match(p.re);
        if (hits) add('FAIL', `${p.label} が残っています: ${[...new Set(hits)].slice(0, 5).join('、')}`);
      }
      if (info.sampleBar) add('FAIL', '「制作サンプル」の帯（.sample-bar）が残っています');

      for (const img of info.imgs) {
        if (img.alt === null || img.alt.trim() === '') add('WARN', `alt のない画像: ${img.src}`);
        if (img.src && !/^(https?:|data:)/.test(img.src)) {
          const local = path.resolve(path.dirname(indexPath), img.src.split(/[?#]/)[0]);
          if (!fs.existsSync(local)) add('FAIL', `画像ファイルが見つかりません: ${img.src}`);
        }
        if (/unsplash|pexels|pixabay/.test(img.src)) add('INFO', `フリー素材の画像を使っています（お客さんに伝える）: ${img.src.slice(0, 60)}`);
      }

      if (info.phoneLike > 0 && info.telLinks === 0) add('WARN', '電話番号がありますが、押して電話できるリンク（tel:）がありません');
      if (!info.title) add('FAIL', '<title> がありません');
      if (!info.description) add('WARN', '<meta name="description"> がありません');
      if (!info.viewportMeta) add('FAIL', '<meta name="viewport"> がないため、スマホで小さく表示されます');
      add('INFO',
        info.noindex
          ? 'noindex が入っています（確認中なら正しい。納品前に外す）'
          : 'noindex は入っていません（納品版なら正しい。確認用に公開するなら入れる）');
    }
    await page.close();
  }

  // CSS の背景画像などで参照しているローカルファイルも確認する
  const html = fs.readFileSync(indexPath, 'utf8');
  for (const m of html.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/g)) {
    const ref = m[1];
    if (/^(https?:|data:)/.test(ref)) continue;
    const local = path.resolve(path.dirname(indexPath), ref.split(/[?#]/)[0]);
    if (!fs.existsSync(local)) add('FAIL', `CSSで指定している画像ファイルが見つかりません: ${ref}`);
  }

  await browser.close();

  const order = { FAIL: 0, WARN: 1, OK: 2, INFO: 3 };
  results.sort((a, b) => order[a.level] - order[b.level]);
  console.log(`\n=== ${slug} のチェック結果 ===`);
  for (const r of results) console.log(`[${r.level}] ${r.msg}`);
  const fails = results.filter((r) => r.level === 'FAIL').length;
  const warns = results.filter((r) => r.level === 'WARN').length;
  console.log(`\nFAIL ${fails}件 / WARN ${warns}件`);
  process.exit(fails > 0 ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(2);
});
