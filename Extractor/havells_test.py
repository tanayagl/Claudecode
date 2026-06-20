#!/usr/bin/env python3
"""
Test scraper - runs for ONE state only (CHHATTISGARH) to verify dealer data loads.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

URL        = "https://www.havells.com/store-locator"
TEST_STATE = "CHHATTISGARH"


def make_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")
    return webdriver.Chrome(options=opts)


def js_select(driver, element, value):
    """Select a value and dispatch change event so JS frameworks pick it up."""
    driver.execute_script("""
        var sel = arguments[0];
        sel.value = arguments[1];
        sel.dispatchEvent(new Event('change', {bubbles: true}));
        sel.dispatchEvent(new Event('input',  {bubbles: true}));
    """, element, value)


def main():
    driver = make_driver()

    try:
        driver.get(URL)
        print("Loaded page, waiting 5s for JS...")
        time.sleep(5)

        # Print all selects found
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"\nFound {len(selects)} <select> elements:")
        for i, sel in enumerate(selects):
            opts = [(o.get_attribute("value"), o.text.strip()) for o in Select(sel).options]
            print(f"  [{i}] {opts[:6]}")

        # Find type select
        type_sel = None
        for sel in selects:
            if any(o.text.strip() == "Dealer Locator" for o in Select(sel).options):
                type_sel = sel
                break

        if not type_sel:
            print("ERROR: Type dropdown not found")
            return

        # Select Dealer Locator via JS event
        dl_value = next(o.get_attribute("value") for o in Select(type_sel).options
                        if o.text.strip() == "Dealer Locator")
        js_select(driver, type_sel, dl_value)
        print(f"\nSelected Dealer Locator (value={dl_value})")
        time.sleep(3)

        # Find state select
        selects = driver.find_elements(By.TAG_NAME, "select")
        SKIP = {"", "Select Type", "Select State", "Select City", "Select Category",
                "Dealer Locator", "Exclusive Brand Stores", "Utsav Stores",
                "Branches", "Experience Centre"}
        state_sel = None
        state_val = None
        for sel in selects:
            opts = [(o.get_attribute("value"), o.text.strip()) for o in Select(sel).options]
            real = [(v, t) for v, t in opts if t not in SKIP and v]
            if len(real) > 5:
                state_sel = sel
                # Find CHHATTISGARH
                for v, t in real:
                    if TEST_STATE in t:
                        state_val = v
                        break
                break

        if not state_sel or not state_val:
            print("ERROR: State dropdown or CHHATTISGARH not found")
            return

        js_select(driver, state_sel, state_val)
        print(f"Selected state: {TEST_STATE} (value={state_val})")
        time.sleep(2)

        # Find and click Submit
        submit = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip().lower() == "submit":
                submit = btn
                break

        if not submit:
            print("ERROR: Submit button not found")
            return

        print(f"Clicking Submit...")
        driver.execute_script("arguments[0].click();", submit)

        # Wait up to 20s for District: to appear
        print("Waiting for dealer results...")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: "District:" in d.find_element(By.CSS_SELECTOR, "#store_locator_list").text
            )
            print("✓ Dealer results loaded!")
        except TimeoutException:
            print("✗ Timed out — no dealer data appeared")

        result_text = driver.find_element(By.CSS_SELECTOR, "#store_locator_list").text
        result_html = driver.find_element(By.CSS_SELECTOR, "#store_locator_list").get_attribute("innerHTML")

        print(f"\n--- RESULT TEXT (first 1000 chars) ---")
        print(result_text[:1000])

        # Save for inspection
        with open("test_output.json", "w", encoding="utf-8") as f:
            json.dump({"state": TEST_STATE, "html": result_html, "text": result_text}, f,
                      ensure_ascii=False, indent=2)
        print(f"\nFull output saved to test_output.json")
        print(f"Total chars in result: {len(result_text)}")
        print(f"Dealer count (District: occurrences): {result_text.count('District:')}")

        input("\nBrowser open — press Enter to close...")

    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
