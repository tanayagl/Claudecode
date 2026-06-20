import asyncio
import csv
import sys
from playwright.async_api import async_playwright

SEARCH_KEYWORD = "Electric"
OUTPUT_FILE = "results.csv"
MAX_RESULTS = 100  # scroll limit guard


async def scrape_google_maps(keyword: str) -> list[dict]:
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        search_url = f"https://www.google.com/maps/search/{keyword.replace(' ', '+')}"
        print(f"Navigating to: {search_url}")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Dismiss cookie/consent dialogs if present
        for selector in ['button[aria-label*="Accept"]', 'button[aria-label*="Reject"]', '#L2AGLb']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        # Wait for results panel
        results_panel = page.locator('div[role="feed"]')
        await results_panel.wait_for(timeout=15000)

        # Scroll to load all results
        print("Scrolling to load results...")
        prev_count = 0
        stall_count = 0
        while True:
            items = page.locator('div[role="feed"] > div > div > a')
            count = await items.count()
            if count >= MAX_RESULTS:
                break
            await results_panel.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            await page.wait_for_timeout(1500)
            new_count = await items.count()
            if new_count == prev_count:
                stall_count += 1
                if stall_count >= 3:
                    break
            else:
                stall_count = 0
            prev_count = new_count
            print(f"  Loaded {new_count} results so far...")

        # Collect all result URLs first to avoid stale locators
        items = page.locator('div[role="feed"] > div > div > a')
        total = min(await items.count(), MAX_RESULTS)
        print(f"Found {total} results. Collecting URLs...")

        urls = []
        for i in range(total):
            href = await items.nth(i).get_attribute("href")
            if href:
                urls.append(href)

        print(f"Extracting details from {len(urls)} listings...")

        for i, url in enumerate(urls):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(1500)

                name = address = phone = ""

                # Name
                try:
                    name_el = page.locator('h1.DUwDvf, h1[class*="DUwDvf"]').first
                    name = (await name_el.inner_text(timeout=4000)).strip()
                except Exception:
                    pass

                # Address
                try:
                    addr_el = page.locator('button[data-item-id="address"]').first
                    address = (await addr_el.inner_text(timeout=3000)).strip()
                except Exception:
                    pass

                # Phone
                try:
                    phone_el = page.locator('button[data-item-id^="phone:tel:"]').first
                    phone = (await phone_el.inner_text(timeout=3000)).strip()
                except Exception:
                    pass

                if name:
                    results.append({"name": name, "address": address, "phone": phone})
                    print(f"  [{i+1}/{len(urls)}] {name} | {phone or 'N/A'}")
                else:
                    print(f"  [{i+1}/{len(urls)}] Skipped (no name found)")

            except Exception as e:
                print(f"  [{i+1}] Error: {e}", file=sys.stderr)
                continue

        await browser.close()

    return results


def save_csv(data: list[dict], filepath: str):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "phone"])
        writer.writeheader()
        writer.writerows(data)
    print(f"\nSaved {len(data)} records to {filepath}")


async def main():
    keyword = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SEARCH_KEYWORD
    print(f"Searching Google Maps for: {keyword}")
    data = await scrape_google_maps(keyword)
    if data:
        save_csv(data, OUTPUT_FILE)
    else:
        print("No results found.")


if __name__ == "__main__":
    asyncio.run(main())
