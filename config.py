
# --- Scraping Target ---
BASE_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

# --- Output ---
OUTPUT_FILENAME = "amazon_bestsellers.json"


# --- Scraping Parameters ---
DEFAULT_RECORDS_GOAL = 100
DEFAULT_PRODUCTS_TO_DETAIL = 100 # How many products to perform a "deep dive" on.
WEBDRIVER_WAIT_TIMEOUT = 20 # Max seconds to wait for an element to appear.

# --- Random Behavior and Delay Timings to reduce rate limiting (in seconds) ---
DELAYS = {
    "scroll": (2.2, 4.5),           # Wait time between each scroll action.
    "detail_page": (6.0, 12.0),      # Wait time before scraping a product detail page.
    "next_list_page": (7.0, 15.0)    # Wait time before loading the next list page.
}



# --- CSS Selectors ---
SELECTORS = {
    # Product list page selectors
    "product_container": 'div.zg-grid-general-faceout',
    "next_page_button": "li.a-last a",
    
    # Selectors for data within a product container
    "product_name": 'div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1',
    "price": 'span._cDEzb_p13n-sc-price_3mJ9Z',
    "rating": 'span.a-icon-alt',
    "num_reviews": 'span.a-size-small',
    "product_url": [
        'a.a-link-normal.aok-block',  # Primary, more specific selector
        'a.a-link-normal'             # Fallback, more general selector
    ],
    
    # Product detail page selectors
    "seller_info": [
        'div#merchant-info',          # Primary buy-box on the right side
        'div#sellerProfileTriggerId', # Link with the seller's name
        'div#bylineInfo'              # Byline under the product title
    ],
    "review_text": 'div[data-hook="review-collapsed"] span'
}

# --- Browser and Stealth Options ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
CHROME_ARGUMENTS = [
    "--headless",
    "--window-size=1920,1080",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    '--ignore-certificate-errors' # To handle SSL handshake issues on certain networks
]
CHROME_EXPERIMENTAL_OPTIONS = {
    "excludeSwitches": ["enable-automation"],
    "useAutomationExtension": False
}
