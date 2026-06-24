#!/usr/bin/env python3
"""Capture exact POST bodies sent to Havells storelocator API endpoints."""
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
js_select(driver, selects[0], "dealer")
time.sleep(2)
selects = driver.find_elements(By.TAG_NAME, "select")
js_select(driver, selects[1], "CHHATTISGARH")
time.sleep(1)
for btn in driver.find_elements(By.TAG_NAME, "button"):
    if btn.text.strip().lower() == "submit":
        driver.execute_script("arguments[0].click();", btn)
        break

WebDriverWait(driver, 20).until(
    lambda d: "District:" in d.find_element(By.CSS_SELECTOR, "#store_locator_list").text
)

logs = driver.get_log("performance")
for entry in logs:
    msg = json.loads(entry["message"])["message"]
    if msg.get("method") == "Network.requestWillBeSent":
        try:
            req = msg["params"]["request"]
            url = req.get("url","")
            if "storelocator" in url:
                print(f"\nURL: {url}")
                print(f"Method: {req.get('method')}")
                print(f"Headers: {json.dumps(dict(req.get('headers',{})), indent=2)}")
                print(f"POST body: {req.get('postData','(none)')}")
        except Exception:
            pass

driver.quit()
