import os
import ctypes
import time
import logging
from datetime import date
from dotenv import load_dotenv
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
import selenium.webdriver.support.expected_conditions as EC

import config_example as cfg
from notifier import EmailNotifier
from utils.email_utils import build_tender_email_body
from utils.date_utils import today_str

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger('main')

CARRIER_IDS = 'CARRIER_A,CARRIER_B'
TENDER_STATUS_VALUES = [
    'STATUS_1',
    'STATUS_2',
    'STATUS_3',
]
TO_LIST_VALUES = ['LoadID', 'CarrierCode', 'Service', 'Status', 'TenderedBy', 'ResponseReasonCode', 'DestLocation', 'ID']


class TenderCrawl:
    def __init__(self, username, password, download_path):
        option = webdriver.ChromeOptions()
        prefs = {"download.default_directory": str(download_path)}
        option.add_experimental_option("prefs", prefs)
        service = Service(r"C:\chromedriver.exe")
        self.driver = webdriver.Chrome(service=service, options=option)

        winapi = ctypes.windll.user32
        width = winapi.GetSystemMetrics(0)
        height = winapi.GetSystemMetrics(1)
        self.driver.set_window_size(width, height)
        self.driver.maximize_window()

        self.driver.get(cfg.TMS_URL)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'i2ui_shell_content')))
        self.driver.switch_to.frame(self.driver.find_element('name', 'i2ui_shell_content'))
        self.driver.switch_to.frame(self.driver.find_element('id', 'resultFrame'))
        self.driver.find_element('name', 'loginUser').send_keys(username)
        self.driver.find_element('id', 'dspLoginPassword').send_keys(password)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.loginInner'))).click()
        log.info("Login complete")

    def switch_to_nav(self):
        self.driver.switch_to.default_content()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'i2ui_shell_content')))
        self.driver.switch_to.frame(self.driver.find_element('name', 'i2ui_shell_content'))
        self.driver.switch_to.frame(self.driver.find_element('id', 'navFrame'))

    def switch_to_result(self):
        self.driver.switch_to.default_content()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'i2ui_shell_content')))
        self.driver.switch_to.frame(self.driver.find_element('name', 'i2ui_shell_content'))
        self.driver.switch_to.frame(self.driver.find_element('id', 'resultFrame'))

    def navigate_to_tender_request(self):
        self.switch_to_nav()
        time.sleep(1)
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'TREECELLIMAGE_navigation_navigation_8'))).click()
        time.sleep(1)
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="TREECELL_navigation_8_1"]/a[2]'))).click()
        log.info("Navigated to Tender Requests")

    def set_search_conditions(self):
        self.switch_to_result()

        log.info("Selecting System Default saved search")
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.NAME, 'savedSearches')))
        Select(self.driver.find_element(By.NAME, 'savedSearches')).select_by_visible_text('System Default')

        self.driver.find_element(By.ID, 'principalID').clear()

        self.switch_to_result()
        time.sleep(5)

        log.info("Clicking Search button")
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//img[@alt="Search"]'))).click()

        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.NAME, 'carrierID')))

        # status_ is a hidden select — manipulated via JS to avoid element not interactable errors
        log.info("Selecting tender status values")
        select_elem = self.driver.find_element(By.NAME, 'status_')
        self.driver.execute_script("""
            var select = arguments[0];
            var values = arguments[1];
            for (var i = 0; i < select.options.length; i++) {
                select.options[i].selected = values.indexOf(select.options[i].value) >= 0;
            }
            status_tmcombobox.showSelected();
        """, select_elem, TENDER_STATUS_VALUES)

        log.info("Entering carrier ID")
        carrier = self.driver.find_element(By.NAME, 'carrierID')
        carrier.clear()
        carrier.send_keys(CARRIER_IDS)

        log.info("Expanding date section")
        expand_btn = self.driver.find_element(By.CSS_SELECTOR, '#loadDatesSearchSection img[src*="container_expand"]')
        self.driver.execute_script("arguments[0].click();", expand_btn)

        log.info("Setting date range to TODAY")
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.NAME, 'tenderResponseRequiredFromRelativeDateKeyword')))
        Select(self.driver.find_element(By.NAME, 'tenderResponseRequiredFromRelativeDateKeyword')).select_by_value('TODAY')
        Select(self.driver.find_element(By.NAME, 'tenderResponseRequiredToRelativeDateKeyword')).select_by_value('TODAY')

        log.info("Submitting search")
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@href,"submitSearch")]'))).click()
        log.info(f"Search submitted — Carrier: {CARRIER_IDS}")
        time.sleep(5)

    def customize_columns(self):
        self.switch_to_result()

        log.info("Clicking List Customization")
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//img[@alt="List Customization"]'))).click()

        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.NAME, 'toList')))

        # Move unwanted columns back to fromList
        self.driver.execute_script("""
            var keep = arguments[0];
            var toList = document.ListCustomizationForm.toList;
            for (var i = 0; i < toList.options.length; i++) {
                toList.options[i].selected = keep.indexOf(toList.options[i].value) < 0;
            }
            tmuiduallistboxmoveit(toList, document.ListCustomizationForm.fromList, mandatoryColumns, null, true);
        """, TO_LIST_VALUES)

        # Move desired columns into toList
        self.driver.execute_script("""
            var keep = arguments[0];
            var toList = document.ListCustomizationForm.toList;
            var toValues = Array.from(toList.options).map(function(o) { return o.value; });
            var fromList = document.ListCustomizationForm.fromList;
            for (var i = 0; i < fromList.options.length; i++) {
                fromList.options[i].selected = keep.indexOf(fromList.options[i].value) >= 0 && toValues.indexOf(fromList.options[i].value) < 0;
            }
            tmuiduallistboxmoveit(fromList, toList);
        """, TO_LIST_VALUES)

        # Reorder toList to match desired column order
        self.driver.execute_script("""
            var order = arguments[0];
            var toList = document.ListCustomizationForm.toList;
            var options = Array.from(toList.options);
            var sorted = order.map(function(v) { return options.find(function(o) { return o.value === v; }); }).filter(Boolean);
            var remaining = options.filter(function(o) { return order.indexOf(o.value) < 0; });
            sorted.concat(remaining).forEach(function(opt) { toList.appendChild(opt); });
        """, TO_LIST_VALUES)

        time.sleep(5)
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(@href,"submitApply")]'))).click()
        time.sleep(3)
        log.info("List Customization complete")

    def export_results(self, download_dir: Path) -> Path:
        self.switch_to_result()

        log.info("Clicking Export Data")
        WebDriverWait(self.driver, 120).until(
            EC.element_to_be_clickable((By.XPATH, '//img[@alt="Export Data"]'))).click()

        log.info("Checking All Rows")
        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.NAME, 'allRows')))
        self.driver.find_element(By.NAME, 'allRows').click()
        time.sleep(10)

        # Submit button is in a popup window
        log.info("Clicking Submit")
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[-1])
        WebDriverWait(self.driver, 120).until(
            EC.element_to_be_clickable((By.ID, 'buttonEmphasized'))).click()

        # Poll for downloaded file (up to 60s)
        end_time = time.time() + 60
        file = None
        while time.time() < end_time:
            for f in download_dir.iterdir():
                if f.suffix == '.xlsx' and 'TM_ExportData' in f.name:
                    file = f
                    break
            if file:
                break
            time.sleep(1)

        # Close popup
        handles = self.driver.window_handles
        if len(handles) > 1:
            self.driver.switch_to.window(handles[-1])
            self.driver.close()
            self.driver.switch_to.window(handles[0])

        # Click Cancel to return to main page
        self.switch_to_result()
        WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.ID, 'buttonRegular'))).click()

        if not file:
            log.warning("No download file found")
            return None

        today = date.today().strftime('%m%d%Y')
        save_path = download_dir / f'TenderStatus_{today}.xlsx'
        if save_path.exists():
            save_path.unlink()
        file.rename(save_path)
        log.info(f"Export complete: {save_path.name}")
        return save_path

    def quit(self):
        self.driver.quit()


if __name__ == '__main__':
    load_dotenv(cfg.ENV_PATH)
    username = os.getenv(cfg.TMS_USER_ENV)
    password = os.getenv(cfg.TMS_PASS_ENV)

    download_dir = cfg.DOWNLOAD_BASE
    download_dir.mkdir(parents=True, exist_ok=True)

    # Remove oldest files if at or above the limit
    existing = sorted(download_dir.glob('TenderStatus_*.xlsx'), key=lambda f: f.stat().st_mtime)
    for old_file in existing[:-cfg.MAX_DATA_FOLDERS + 1] if len(existing) >= cfg.MAX_DATA_FOLDERS else []:
        old_file.unlink()
        log.info(f"Deleted old file: {old_file.name}")

    crawl = None
    exported_file = None
    try:
        crawl = TenderCrawl(username, password, download_dir)
        crawl.navigate_to_tender_request()
        crawl.set_search_conditions()
        crawl.customize_columns()

        for attempt in range(5):
            log.info(f"Export attempt {attempt + 1}/5")
            exported_file = crawl.export_results(download_dir)
            if exported_file:
                break
            log.warning("Retrying")
    except Exception as e:
        log.warning(f"Error: {e}")
    finally:
        if crawl:
            crawl.quit()

    if exported_file:
        smtp_user = os.getenv(cfg.SMTP_USER_ENV)
        smtp_pass = os.getenv(cfg.SMTP_PASS_ENV)
        date_today = today_str('h')
        body = build_tender_email_body(exported_file, date_today)
        notifier = EmailNotifier(smtp_user, smtp_pass)
        notifier.send(
            subject=cfg.EMAIL_SUBJECT.format(date_today),
            body=body,
            to=cfg.EMAIL_TO,
            cc=cfg.EMAIL_CC,
            sender=cfg.EMAIL_FROM,
            attachment_path=exported_file,
        )

    log.info("Done")
