const { chromium } = require('playwright');
const path = require('path');
const [, , inputPath] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('main: ' + e.message));

  await page.goto('file://' + path.resolve(inputPath));
  await page.waitForTimeout(300);
  await page.click('.row-head');
  await page.waitForTimeout(200);

  // check download link href looks like a valid data URI
  const downloadHref = await page.getAttribute('a[download$=".html"]', 'href');

  // click "open in new tab" and capture the popup
  const [popup] = await Promise.all([
    context.waitForEvent('page'),
    page.click('button:has-text("Open resume in new tab")'),
  ]);
  await popup.waitForLoadState('load');
  await popup.waitForTimeout(400);
  const popupTitle = await popup.title();
  const popupHasContent = (await popup.content()).includes('AMAN RANJAN');

  console.log(JSON.stringify({
    errors,
    downloadHrefPrefix: downloadHref ? downloadHref.slice(0, 40) : null,
    popupTitle,
    popupHasContent,
    popupUrl: popup.url(),
  }, null, 2));

  await browser.close();
})();
