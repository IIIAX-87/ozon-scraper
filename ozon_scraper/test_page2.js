const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
	const browser = await chromium.launch({ headless: true });
	const context = await browser.newContext({
		userAgent:
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		locale: "ru-RU",
		viewport: { width: 1920, height: 1080 },
	});
	const page = await context.newPage();
	try {
		const url = "https://am.ozon.com/seller/swikki-1313863/products/";
		await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
		console.log("loaded", page.url());
		console.log("title", await page.title());
		const html = await page.content();
		fs.writeFileSync("/tmp/ozon_page_am.html", html);
	} catch (e) {
		console.error("ERR", e.message);
	}
	await browser.close();
})();
