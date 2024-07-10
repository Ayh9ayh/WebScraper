import csv
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class GoogleMapScraper:
    def __init__(self):
        self.output_file_name = "google_map_business_data.csv"
        self.headless = False
        self.driver = None
        self.unique_check = set()

    def config_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def save_data(self, data):
        file_exists = os.path.isfile(self.output_file_name)
        header = ['name', 'rating', 'reviews_count', 'address', 'category', 'phone', 'website']
        with open(self.output_file_name, 'a', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(header)
            writer.writerow(data)

    def parse_rating_and_review_count(self, business):
        try:
            reviews_block = business.find_element(By.CLASS_NAME, 'AJB7ye').text.split("(")
            rating = reviews_block[0].strip()
            reviews_count = reviews_block[1].split(")")[0].strip()
        except (NoSuchElementException, IndexError):
            rating = ""
            reviews_count = ""
        return rating, reviews_count

    def parse_address_and_category(self, business):
        try:
            address_block = business.find_elements(By.CLASS_NAME, "W4Efsd")[2].text.split("·")
            if len(address_block) >= 2:
                address = address_block[1].strip()
                category = address_block[0].strip()
            elif len(address_block) == 1:
                address = ""
                category = address_block[0].strip()
        except (NoSuchElementException, IndexError):
            address = ""
            category = ""
        return address, category

    def extract_phone_and_website(self):
        phone = ""
        website = ""
        try:
            phone_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-item-id='telephone']//span[@class='Io6YTe fontBodyMedium']"))
            )
            phone = phone_element.text
        except (NoSuchElementException, TimeoutException):
            phone = ""

        try:
            website_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@data-item-id='authority']"))
            )
            website = website_element.get_attribute('href')
        except (NoSuchElementException, TimeoutException):
            website = ""

        return phone, website

    def get_business_info(self):
        time.sleep(2)
        businesses = self.driver.find_elements(By.CLASS_NAME, 'THOPZb')
        for business in businesses:
            name = business.find_element(By.CLASS_NAME, 'fontHeadlineSmall').text
            rating, reviews_count = self.parse_rating_and_review_count(business)
            address, category = self.parse_address_and_category(business)
            
            # Click on the business to load more details
            try:
                business.click()
                time.sleep(2)  # Wait for the business details to load
                
                # Extract phone number and website
                phone, website = self.extract_phone_and_website()
            except NoSuchElementException:
                phone = ""
                website = ""

            unique_id = "".join([name, rating, reviews_count, address, category, phone, website])
            if unique_id not in self.unique_check:
                data = [name, rating, reviews_count, address, category, phone, website]
                self.save_data(data)
                self.unique_check.add(unique_id)

    def load_companies(self, url, max_scroll=2):
        print("Getting business info", url)
        self.driver.get(url)
        time.sleep(5)
        panel_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[1]'
        scrollable_div = self.driver.find_element(By.XPATH, panel_xpath)
        flag = True
        i = 0
        while flag and i < max_scroll:
            print(f"Scrolling to page {i + 2}")
            self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(2)

            if "You've reached the end of the list." in self.driver.page_source:
                flag = False

            self.get_business_info()
            i += 1

if __name__ == "__main__":
    url = input("Enter Google Maps search URL: ")
    business_scraper = GoogleMapScraper()
    business_scraper.config_driver()
    business_scraper.load_companies(url, max_scroll=2)
    business_scraper.driver.quit()