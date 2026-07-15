// Verifies whether a Playwright storageState actually results in a logged-in
// Indeed session, without submitting or clicking anything. Screenshots the
// result for manual inspection.
const { chromium } = require('playwright');
const path = require('path');
const [, , storageStatePath, screenshotPath] = process.argv;

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    proxy: { server: process.env.HTTPS_PROXY || 'http://127.0.0.1:37957' },
  });
  const context = await browser.newContext({ storageState: path.resolve(storageStatePath) });
  const page = await context.newPage();
  await page.goto('https://in.indeed.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);

  const bodyText = await page.evaluate(() => document.body.innerText);
  const title = await page.title();
  const url = page.url();

  // Look for common signed-in indicators without assuming exact markup.
  const signedInHints = ['Sign out', 'My jobs', 'Applications', 'Job seeker'];
  const signedOutHints = ['Sign in', 'Employer / Post Job'];
  const foundSignedIn = signedInHints.filter(h => bodyText.includes(h));
  const foundSignedOut = signedOutHints.filter(h => bodyText.includes(h));

  await page.screenshot({ path: path.resolve(screenshotPath), fullPage: false });

  console.log(JSON.stringify({ url, title, foundSignedIn, foundSignedOut }, null, 2));
  await browser.close();
})();
