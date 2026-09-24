#!/usr/bin/env node
// 見積書・請求書のPDFを作る。
// 使い方: node .claude/skills/client-site/scripts/make_document.cjs private/billing/<ファイル名>.json
// 差出人の情報は private/profile.json から読む（公開リポジトリに入れないため、private/ は .gitignore 済み）。
// PDF は入力の JSON と同じフォルダに、同じ名前で作られる。

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

// 日本語フォントを .check/fonts に用意する。取れなければ端末のフォントで作る。
function ensureFonts() {
  const dir = path.resolve('.check', 'fonts');
  fs.mkdirSync(dir, { recursive: true });
  const faces = [];
  for (const weight of [400, 700]) {
    const file = path.join(dir, `noto-sans-jp-${weight}.ttf`);
    if (!fs.existsSync(file)) {
      try {
        const css = execSync(
          `curl -sf -A "Mozilla/5.0 Chrome/120" "https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@${weight}"`
        ).toString();
        const url = (css.match(/https:\/\/fonts\.gstatic\.com[^)]+/) || [])[0];
        if (url) execSync(`curl -sf -o "${file}" "${url}"`);
      } catch {
        // ネットにつながらないときは端末のフォントを使う
      }
    }
    if (fs.existsSync(file)) {
      faces.push(`@font-face { font-family: DocFont; src: url("file://${file}"); font-weight: ${weight}; }`);
    }
  }
  return faces.join('\n');
}

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const yen = (n) => '¥' + Number(n).toLocaleString('ja-JP');
const jpDate = (iso) => {
  const [y, m, d] = String(iso).split('-').map(Number);
  return `${y}年${m}月${d}日`;
};

const dataPath = process.argv[2];
if (!dataPath) {
  console.error('使い方: node make_document.cjs private/billing/<ファイル名>.json');
  process.exit(2);
}
const doc = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const profilePath = path.resolve('private', 'profile.json');
if (!fs.existsSync(profilePath)) {
  console.error('private/profile.json がありません。差出人の名前などを先に登録してください。');
  process.exit(2);
}
const me = JSON.parse(fs.readFileSync(profilePath, 'utf8'));

const isEstimate = doc.type === 'estimate';
if (!isEstimate && doc.type !== 'invoice') {
  console.error('type は "estimate"（見積書）か "invoice"（請求書）にしてください。');
  process.exit(2);
}
const title = isEstimate ? '御見積書' : '請求書';
const total = doc.items.reduce((sum, it) => sum + it.qty * it.price, 0);

// ココナラなどを通した取引では、振込先や連絡先を書くとサイトの外でのやりとりになってしまう。
// そのため platform のときは振込先も連絡先も載せない。
if (!['platform', 'bank'].includes(doc.payment)) {
  console.error('payment は "platform"（ココナラなど経由）か "bank"（振込）にしてください。');
  process.exit(2);
}
if (doc.payment === 'bank' && !me.bank) {
  console.error('支払い方法が振込ですが、private/profile.json に振込先（bank）がありません。');
  process.exit(2);
}
const paymentText = {
  platform: `${esc(doc.platform || 'ココナラ')}の取引画面からお支払いください。`,
  bank: me.bank
    ? `下記の口座へお振り込みください（振込手数料はご負担をお願いいたします）。<br>${esc(me.bank.bankName)} ${esc(me.bank.branch)} ${esc(me.bank.accountType)} ${esc(me.bank.accountNumber)}<br>口座名義：${esc(me.bank.accountHolder)}`
    : '',
}[doc.payment];

const rows = doc.items.map((it) => `
  <tr>
    <td>${esc(it.name)}${it.note ? `<div class="note">${esc(it.note)}</div>` : ''}</td>
    <td class="num">${it.qty}</td>
    <td class="c">${esc(it.unit || '式')}</td>
    <td class="num">${yen(it.price)}</td>
    <td class="num">${yen(it.qty * it.price)}</td>
  </tr>`).join('');

const html = `<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>
${ensureFonts()}
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: DocFont, "Noto Sans CJK JP", "Hiragino Sans", sans-serif; color: #1f2933; font-size: 10.5pt; line-height: 1.6; }
h1 { text-align: center; font-size: 20pt; letter-spacing: .4em; border-bottom: 2px solid #1f2933; padding-bottom: 6px; margin-bottom: 18px; }
.meta { text-align: right; font-size: 9.5pt; }
.head { display: flex; justify-content: space-between; align-items: flex-start; margin-top: 14px; gap: 24px; }
.to { font-size: 14pt; font-weight: 700; border-bottom: 1px solid #1f2933; padding-bottom: 2px; min-width: 60%; }
.from { font-size: 9.5pt; text-align: right; white-space: pre-line; }
.from .name { font-size: 11pt; font-weight: 700; }
.lead { margin-top: 18px; }
.total { margin-top: 12px; display: inline-flex; align-items: baseline; gap: 18px; border-bottom: 3px double #1f2933; padding: 4px 4px 6px; }
.total .label { font-weight: 700; }
.total .amount { font-size: 18pt; font-weight: 700; }
.info { margin-top: 12px; font-size: 9.5pt; }
.info dt { float: left; width: 6.5em; font-weight: 700; }
.info dd { margin-left: 6.5em; }
table { width: 100%; border-collapse: collapse; margin-top: 18px; }
th { background: #eef2f7; font-weight: 700; font-size: 9.5pt; }
th, td { border: 1px solid #b8c2cc; padding: 7px 8px; vertical-align: top; }
td.num { text-align: right; white-space: nowrap; }
td.c { text-align: center; }
.note { font-size: 8.5pt; color: #52606d; }
tfoot td { font-weight: 700; }
.remarks { margin-top: 18px; border: 1px solid #b8c2cc; padding: 10px 12px; font-size: 9.5pt; white-space: pre-line; }
.remarks strong { display: block; margin-bottom: 4px; }
</style></head><body>
<h1>${title}</h1>
<div class="meta">${isEstimate ? '見積番号' : '請求番号'}：${esc(doc.number)}<br>発行日：${jpDate(doc.date)}</div>
<div class="head">
  <div class="to">${esc(doc.client)} ${esc(doc.honorific || '様')}</div>
  <div class="from"><span class="name">${esc(me.name)}</span>${me.address ? '\n' + esc(me.address) : ''}${me.contact && doc.payment !== 'platform' ? '\n' + esc(me.contact) : ''}</div>
</div>
<p class="lead">${isEstimate ? '下記のとおり、お見積もり申し上げます。' : '下記のとおり、ご請求申し上げます。'}</p>
<div class="total"><span class="label">${isEstimate ? 'お見積金額' : 'ご請求金額'}（税込）</span><span class="amount">${yen(total)}</span></div>
<dl class="info">
  <dt>件名</dt><dd>${esc(doc.subject)}</dd>
  ${isEstimate
    ? `<dt>有効期限</dt><dd>${jpDate(doc.validUntil)}</dd>${doc.delivery ? `<dt>納期</dt><dd>${esc(doc.delivery)}</dd>` : ''}`
    : `<dt>お支払期限</dt><dd>${jpDate(doc.dueDate)}</dd>`}
  <dt>お支払方法</dt><dd>${paymentText}</dd>
</dl>
<table>
  <thead><tr><th>内容</th><th style="width:9%">数量</th><th style="width:9%">単位</th><th style="width:16%">単価（税込）</th><th style="width:17%">金額（税込）</th></tr></thead>
  <tbody>${rows}</tbody>
  <tfoot><tr><td colspan="4" style="text-align:right">合計（税込）</td><td class="num">${yen(total)}</td></tr></tfoot>
</table>
${doc.notes ? `<div class="remarks"><strong>備考</strong>${esc(doc.notes)}</div>` : ''}
</body></html>`;

(async () => {
  const { chromium } = loadPlaywright();
  const launchOpts = {};
  if (fs.existsSync('/opt/pw-browsers/chromium')) launchOpts.executablePath = '/opt/pw-browsers/chromium';
  const browser = await chromium.launch(launchOpts);
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const out = dataPath.replace(/\.json$/, '.pdf');
  await page.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true });
  // --png を付けると、スマホで中身を確かめやすいように同じ内容の画像も作る
  if (process.argv.includes('--png')) {
    await page.setViewportSize({ width: 794, height: 1123 });
    await page.addStyleTag({ content: 'body { padding: 68px 60px; }' });
    await page.screenshot({ path: out.replace(/\.pdf$/, '.png'), fullPage: true });
  }
  await browser.close();
  console.log(`${title}を作りました: ${out}（合計 ${yen(total)}）`);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
