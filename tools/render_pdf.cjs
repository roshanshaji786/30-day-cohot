/**
 * Print an HTML file to A4 PDF with page numbers.
 *
 * Usage: node tools/render_pdf.cjs <input.html> <output.pdf>
 *
 * Uses the sandbox Chromium installed by theme-v17/tools/setup-renderer.sh.
 */
const puppeteer = require('/tmp/btest/node_modules/puppeteer');

(async () => {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) {
    console.error('usage: node render_pdf.cjs <input.html> <output.pdf>');
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    executablePath: '/tmp/chromium-bin',
    headless: 'shell',
    args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
  });
  const page = await browser.newPage();
  await page.goto('file://' + input, { waitUntil: 'load' });
  await page.evaluateHandle('document.fonts.ready');

  const footer = `
    <div style="width:100%;font-size:7.2px;color:#6b6b7b;font-family:'DejaVu Sans',sans-serif;
                padding:0 14mm;display:flex;justify-content:space-between;align-items:center;">
      <span>Test report &nbsp;&middot;&nbsp; learn.dartsai.in production-readiness audit &nbsp;&middot;&nbsp; 30 September 2026</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>`;

  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: footer,
    margin: { top: '16mm', bottom: '17mm', left: '14mm', right: '14mm' },
  });

  await browser.close();
  console.log('wrote ' + output);
})();
