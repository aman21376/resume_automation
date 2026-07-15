// Renders an HTML file to a one-page A4 PDF. Usage: node render_pdf.js <input.html> <output.pdf>
const { chromium } = require('playwright');
const path = require('path');

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error('Usage: node render_pdf.js <input.html> <output.pdf>');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(inputPath));
  await page.pdf({
    path: path.resolve(outputPath),
    format: 'A4',
    printBackground: true,
    margin: { top: '0', bottom: '0', left: '0', right: '0' }
  });
  await browser.close();
})();
