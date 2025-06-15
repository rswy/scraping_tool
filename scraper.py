import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1. Import all settings from our configuration file
import config


#  #  #  #  #  #  #  #  #  #  #  #  #  #  
#  Helper Functions
#  #  #  #  #  #  #  #  #  #  #  #  #  #  

# Setting up Chrome WebDriver
def setup_webdriver():
    print("Setting up Chrome WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={config.USER_AGENT}")
    for argument in config.CHROME_ARGUMENTS:
        chrome_options.add_argument(argument)
    for key, value in config.CHROME_EXPERIMENTAL_OPTIONS.items():
        chrome_options.add_experimental_option(key, value)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Command to help hide the 'webdriver' flag from bot detection scripts.
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# Scrolls down the page until no new product containers are dynamically loaded.
def scroll_to_load_more(driver):
    print("...scrolling to load all dynamic content...")
    last_product_count = 0
    while True:
        current_product_count = len(driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["product_container"]))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(random.uniform(*config.DELAYS["scroll"]))

        new_product_count = len(driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["product_container"]))
        if new_product_count == current_product_count:
            print("   ...finished scrolling.")
            break

# Tries to find an element using a list of selectors in a prioritized order.
def find_element_with_fallback(container, selectors):
    if not isinstance(selectors, list):
        selectors = [selectors]

    for selector in selectors:
        try:
            return container.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            continue
    return None

# Scrapes customer review texts from a product detail page.
def scrape_product_details(driver):
    try:
        review_elements = driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["review_text"])
        reviews = [review.text for review in review_elements[:10] if review.text]
    except NoSuchElementException:
        reviews = []
        
    return reviews



#  #  #  #  #  #  #  #  #  #  #  #  #  #  
#  Main Code 
#  #  #  #  #  #  #  #  #  #  #  #  #  #  


# Main function to orchestrate the two-stage scraping process.
def scrape_site(num_records_goal, products_to_detail):
    driver = setup_webdriver()
    wait = WebDriverWait(driver, config.WEBDRIVER_WAIT_TIMEOUT)
    products = []
    current_url = config.BASE_URL
    
    print(f"--- STAGE 1: Scraping list pages until {num_records_goal} products are collected ---")
    while len(products) < num_records_goal and current_url:
        print(f"\nNavigating to list page: {current_url}")
        driver.get(current_url)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS["product_container"])))
            scroll_to_load_more(driver)
            
            product_containers = driver.find_elements(By.CSS_SELECTOR, config.SELECTORS["product_container"])
            
            for container in product_containers:
                if len(products) >= num_records_goal:
                    break
                
                url_element = find_element_with_fallback(container, config.SELECTORS["product_url"])
                if url_element:
                    product_url = url_element.get_attribute('href')
                else:
                    continue
                
                if not any(p['product_url'] == product_url for p in products):
                    name_element = find_element_with_fallback(container, config.SELECTORS["product_name"])
                    price_element = find_element_with_fallback(container, config.SELECTORS["price"])
                    rating_element = find_element_with_fallback(container, config.SELECTORS["rating"])
                    num_reviews_element = find_element_with_fallback(container, config.SELECTORS["num_reviews"])
                    
                    products.append({
                        'product_url': product_url,
                        'product_name': name_element.text if name_element else "N/A",
                        'price': price_element.text if price_element else "N/A",
                        'rating': rating_element.get_attribute('innerHTML').split(' ')[0] if rating_element else "N/A",
                        'num_reviews': num_reviews_element.text if num_reviews_element else "0"
                    })

            next_page_element = find_element_with_fallback(driver, config.SELECTORS["next_page_button"])
            if next_page_element:
                current_url = next_page_element.get_attribute('href')
                time.sleep(random.uniform(*config.DELAYS["next_list_page"]))
            else:
                print("No more 'Next Page' buttons found. Ending list scrape.")
                current_url = None

        except TimeoutException:
            print(f"FATAL ERROR: Timed out on page: {current_url}. View debug screenshot for an idea of what went wrong!")
            driver.save_screenshot('debug_screenshot.png')
            break

    print(f"\n--- STAGE 1 COMPLETE: Collected {len(products)} unique products. ---")


    print(f"\n--- STAGE 2: Scraping reviews for top {products_to_detail} products ---")
    for i, product in enumerate(products[:products_to_detail]):
        if product.get('product_url') and product.get('product_url') != "N/A":
            print(f"Scraping reviews for product {i+1}/{products_to_detail}: {product['product_name'][:30]}...")
            driver.get(product['product_url'])
            time.sleep(random.uniform(*config.DELAYS["detail_page"]))
            reviews = scrape_product_details(driver)
            product['reviews'] = reviews
            
    driver.quit()
    print("\n--- Scraping process finished. ---")
    return products






if __name__ == '__main__':
    scraped_products = scrape_site(
        num_records_goal=config.DEFAULT_RECORDS_GOAL,
        products_to_detail=config.DEFAULT_PRODUCTS_TO_DETAIL
    )
    
    if scraped_products:
        with open(config.OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(scraped_products, f, indent=4, ensure_ascii=False)
        print(f"\nSuccess! Saved {len(scraped_products)} records to {config.OUTPUT_FILENAME}")
    else:
        print("\nScraping failed to produce any data.")