/**
 * Playwright script to check for React hydration mismatch warnings.
 *
 * Usage: node tests/e2e/check_hydration.js <url>
 *
 * Loads the given URL in a headless browser, waits for the page to
 * stabilize, and checks the console for React hydration warnings.
 *
 * Exit codes:
 *   0 — no hydration warnings
 *   1 — hydration warnings found
 *   2 — script error (bad args, page load failure, etc.)
 */

let chromium;
try {
  ({ chromium } = require("playwright"));
} catch {
  console.error("Playwright not installed — run: npm install playwright");
  process.exit(2);
}

const url = process.argv[2];
if (!url) {
  console.error("Usage: node check_hydration.js <url>");
  process.exit(2);
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch();
    const page = await browser.newPage();

    const warnings = [];
    const pageErrors = [];

    page.on("console", (msg) => {
      const text = msg.text();
      if (
        text.includes("did not match") ||
        text.includes("Hydration failed") ||
        text.includes("There was an error while hydrating") ||
        text.includes("switching to client rendering") ||
        text.includes("Text content does not match") ||
        text.includes("Expected server HTML")
      ) {
        warnings.push(text);
      }
    });

    page.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });

    // Wait for any async hydration warnings to surface
    await page.waitForTimeout(2000);

    if (pageErrors.length > 0) {
      console.error("Page errors:");
      pageErrors.forEach((e) => {
        console.error("  ", e);
      });
    }

    if (warnings.length > 0) {
      console.error("Hydration warnings found:");
      warnings.forEach((w) => {
        console.error("  ", w);
      });
      process.exit(1);
    }

    console.log("No hydration warnings detected.");
    process.exit(0);
  } catch (err) {
    console.error("Script error:", err.message);
    process.exit(2);
  } finally {
    if (browser) await browser.close();
  }
})();
