const { chromium } = require('playwright');
const path = require('path');
const [, , inputPath] = process.argv;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const url = 'file://' + path.resolve(inputPath);

  await page.goto(url);
  await page.waitForTimeout(300);

  // expand first row, mark applied
  await page.click('.row-head');
  await page.waitForTimeout(200);
  await page.click('button:has-text("Mark as applied")');
  await page.waitForTimeout(300);

  const newTodayCountAfter = await page.textContent('.view-btn:nth-child(1)');
  const appliedTabCountAfter = await page.textContent('.view-btn.applied-view');

  // switch to Applied view
  await page.click('.view-btn.applied-view');
  await page.waitForTimeout(300);
  const appliedRowCount = await page.$$eval('.row', els => els.length);

  // reload page (simulates hard refresh / redeploy) - localStorage should persist since same file/origin
  await page.reload();
  await page.waitForTimeout(300);
  await page.click('.view-btn.applied-view');
  await page.waitForTimeout(300);
  const appliedRowCountAfterReload = await page.$$eval('.row', els => els.length);

  console.log(JSON.stringify({
    errors,
    newTodayCountAfter,
    appliedTabCountAfter,
    appliedRowCount,
    appliedRowCountAfterReload,
  }, null, 2));

  await page.screenshot({ path: path.resolve(__dirname, '../../applied_view_test.png'), fullPage: false });
  await browser.close();
})();
