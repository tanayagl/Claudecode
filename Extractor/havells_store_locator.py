#!/usr/bin/env python3
"""
Havells Store Locator Scraper - scrapes dealer data for all states.
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

URL         = "https://www.havells.com/store-locator"
OUTPUT_FILE = "havells_dealers.json"


def make_driver():
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")
    return webdriver.Chrome(options=opts)


def wait_for_dealers(driver, timeout=25):
    """Wait until #store_locator_list contains real dealer cards (has 'District:')."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: "District:" in d.find_element(By.CSS_SELECTOR, "#store_locator_list").text
        )
        return True
    except TimeoutException:
        return False


def main():
    driver = make_driver()
    all_data = []

    try:
        driver.get(URL)
        print("Page loaded, waiting for JS to init...")
        time.sleep(5)

        # ── Find all <select> elements and identify type/state dropdowns ──────
        selects = driver.find_elements(By.TAG_NAME, "select")
        print(f"Found {len(selects)} select elements")

        # Print all selects and their options for debugging
        for i, sel in enumerate(selects):
            opts = [(o.get_attribute("value"), o.text.strip()) for o in Select(sel).options]
            print(f"  Select[{i}]: {opts[:5]}")

        # Identify type select (has "Dealer Locator" option)
        type_sel_idx = None
        for i, sel in enumerate(selects):
            texts = [o.text.strip() for o in Select(sel).options]
            if "Dealer Locator" in texts:
                type_sel_idx = i
                break

        if type_sel_idx is None:
            raise RuntimeError("Cannot find Type dropdown")

        # ── Select Dealer Locator ─────────────────────────────────────────────
        type_sel = driver.find_elements(By.TAG_NAME, "select")[type_sel_idx]
        Select(type_sel).select_by_visible_text("Dealer Locator")
        print("Selected: Dealer Locator")
        time.sleep(3)

        # ── Find state dropdown (populated after selecting type) ──────────────
        SKIP = {"", "Select Type", "Select State", "Select City", "Select Category",
                "Dealer Locator", "Exclusive Brand Stores", "Utsav Stores",
                "Branches", "Experience Centre"}

        state_sel_idx = None
        state_options = []
        for i, sel in enumerate(driver.find_elements(By.TAG_NAME, "select")):
            opts = [(o.get_attribute("value"), o.text.strip()) for o in Select(sel).options]
            real = [(v, t) for v, t in opts if t not in SKIP and v]
            if len(real) > 5:   # state dropdown should have many options
                state_sel_idx = i
                state_options = real
                break

        if not state_options:
            raise RuntimeError("Cannot find State dropdown or it's empty")

        print(f"Found {len(state_options)} states")

        # ── Find Submit button ────────────────────────────────────────────────
        submit = None
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if btn.text.strip().lower() == "submit":
                submit = btn
                break
        if submit is None:
            for btn in driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']"):
                submit = btn
                break

        if submit is None:
            raise RuntimeError("Cannot find Submit button")

        print(f"Submit button found: '{submit.text}'")

        # ── Loop through states ───────────────────────────────────────────────
        for idx, (state_val, state_name) in enumerate(state_options):
            print(f"\n[{idx+1}/{len(state_options)}] {state_name} ...", end=" ", flush=True)

            # Re-select Dealer Locator
            selects = driver.find_elements(By.TAG_NAME, "select")
            Select(selects[type_sel_idx]).select_by_visible_text("Dealer Locator")
            time.sleep(1.5)

            # Select state
            selects = driver.find_elements(By.TAG_NAME, "select")
            Select(selects[state_sel_idx]).select_by_value(state_val)
            time.sleep(1)

            # Click Submit
            driver.execute_script("arguments[0].scrollIntoView(true);", submit)
            driver.execute_script("arguments[0].click();", submit)

            # Wait for dealer results
            found = wait_for_dealers(driver, timeout=20)
            html  = driver.find_element(By.CSS_SELECTOR, "#store_locator_list").get_attribute("innerHTML")
            text  = driver.find_element(By.CSS_SELECTOR, "#store_locator_list").text

            dealer_count = text.count("District:")
            print(f"{'✓' if found else '✗'} {dealer_count} dealers")

            all_data.append({
                "state_value": state_val,
                "state_name":  state_name,
                "html":        html,
                "text":        text,
            })

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        driver.quit()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(all_data)} states → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
