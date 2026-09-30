const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({executablePath:'/tmp/chromium-bin', headless:'shell', args:['--no-sandbox','--disable-gpu']});
  const page = await browser.newPage();
  for (const f of ['caseA','caseB','caseC']) {
    await page.goto('file:///tmp/csstest/'+f+'.html');
    const r = await page.evaluate(() => {
      const s = getComputedStyle(document.documentElement);
      const g = (p) => s.getPropertyValue(p).trim() || '(EMPTY)';
      return { accent: g('--c-accent'), pageWidth: g('--page-width'),
               shadow: g('--shadow-lg').slice(0,26), heading: g('--font-heading'),
               probe: getComputedStyle(document.querySelector('#probe')).backgroundColor };
    });
    console.log(f.padEnd(6), JSON.stringify(r));
  }
  await browser.close();
})();
