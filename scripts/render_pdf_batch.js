// Renders every .html file in a directory to a same-named .pdf in an output
// directory, reusing one browser instance (much faster than one process per
// file). Usage: node render_pdf_batch.js <html_dir> <pdf_dir>
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const [, , htmlDir, pdfDir] = process.argv;
if (!htmlDir || !pdfDir) {
  console.error('Usage: node render_pdf_batch.js <html_dir> <pdf_dir>');
  process.exit(1);
}
fs.mkdirSync(pdfDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const files = fs.readdirSync(htmlDir).filter(f => f.endsWith('.html'));
  let done = 0;
  for (const f of files) {
    const base = f.replace(/\.html$/, '');
    await page.goto('file://' + path.resolve(htmlDir, f));
    await page.pdf({
      path: path.resolve(pdfDir, base + '.pdf'),
      format: 'A4', printBackground: true,
      margin: { top: '0', bottom: '0', left: '0', right: '0' },
    });
    done += 1;
    if (done % 25 === 0) console.error(`${done}/${files.length} rendered`);
  }
  console.error(`${done}/${files.length} rendered`);
  await browser.close();
})();
