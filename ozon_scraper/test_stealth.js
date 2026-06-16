const { chromium } = require("playwright");
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
const fs = require("fs");
puppeteer.use(StealthPlugin());

(async () => {
	const execPath = chromium.executablePath();
	console.log("execPath", execPath);
	const browser = await puppeteer.launch({
		headless: "new",
		executablePath: execPath,
		args: [
			"--no-sandbox",
			"--disable-setuid-sandbox",
			"--disable-blink-features=AutomationControlled",
		],
	});
	const page = await browser.newPage();
	try {
		const url = "https://www.ozon.ru/seller/swikki-1313863/products/";
		await page.goto(url, { waitUntil: "networkidle2", timeout: 90000 });
		console.log("loaded", page.url());
		console.log("title", await page.title());
		const html = await page.content();
		fs.writeFileSync("/tmp/ozon_stealth.html", html);
	} catch (e) {
		console.error("ERR", e.message);
	}
	await browser.close();
})();
