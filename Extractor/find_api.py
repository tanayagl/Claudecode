#!/usr/bin/env python3
"""Intercept the AJAX call made by the store locator form to find the API endpoint."""
import time, json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.options import Options

def make_driver():
    opts = Options()
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    opts.add_argument("--no-sandbox")
    return webdriver.Chrome(options=opts)

def js_select(driver, el, value):
    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
        arguments[0].dispatchEvent(new Event('input',  {bubbles:true}));
    """, el, value)

driver = make_driver()
driver.get("https://www.havells.com/store-locator")
time.sleep(5)

selects = driver.find_elements(By.TAG_NAME, "select")
# Select Dealer Locator
js_select(driver, selects[0], "dealer")
time.sleep(2)
# Select CHHATTISGARH
selects = driver.find_elements(By.TAG_NAME, "select")
js_select(driver, selects[1], "CHHATTISGARH")
time.sleep(1)
# Click Submit
for btn in driver.find_elements(By.TAG_NAME, "button"):
    if btn.text.strip().lower() == "submit":
        driver.execute_script("arguments[0].click();", btn)
        break

# Wait for results
WebDriverWait(driver, 20).until(
    lambda d: "District:" in d.find_element(By.CSS_SELECTOR, "#store_locator_list").text
)

# Parse network logs
logs = driver.get_log("performance")
print("=== XHR / Fetch requests ===")
for entry in logs:
    msg = json.loads(entry["message"])["message"]
    if msg.get("method") in ("Network.requestWillBeSent", "Network.responseReceived"):
        try:
            req = msg["params"].get("request") or msg["params"].get("response", {})
            url = req.get("url", "")
            method = req.get("method", "")
            post = req.get("postData", "")
            rtype = msg["params"].get("type","")
            if rtype in ("XHR","Fetch") or "havells" in url:
                print(f"\n[{rtype}] {method} {url}")
                if post:
                    print(f"  POST data: {post}")
        except Exception:
            pass

driver.quit()
