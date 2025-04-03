"""Browser driver setup and management."""

import logging
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

def human_like_delay(min_seconds=2, max_seconds=5):
    """Add a random delay with non-uniform distribution to mimic human behavior."""
    delay = min_seconds + (max_seconds - min_seconds) * (0.5 + 0.5 * (random.random() - 0.5))
    time.sleep(delay)

def scroll_page_gradually(driver):
    """Scroll the page gradually to mimic human reading behavior."""
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    current_position = 0
    
    while current_position < total_height:
        scroll_distance = random.randint(100, viewport_height // 2)
        current_position += scroll_distance
        driver.execute_script(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}})")
        time.sleep(random.uniform(0.5, 2.0))
        if random.random() < 0.2:
            time.sleep(random.uniform(2.0, 4.0))

def check_for_captcha(driver):
    """Check if Google is showing a CAPTCHA or block page."""
    page_text = driver.page_source.lower()
    
    captcha_indicators = [
        "our systems have detected unusual traffic",
        "please show you're not a robot",
        "please solve this captcha",
        "we're sorry...",
        "unusual traffic from your computer network",
        "your computer or network may be sending automated queries"
    ]
    
    for indicator in captcha_indicators:
        if indicator in page_text:
            return True
    
    return False

def create_stealth_driver(headless=False):
    """Create a WebDriver with anti-detection measures."""
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")
    
    # Essential settings to avoid detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Browser settings to appear more human-like
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-US,en;q=0.9")
    
    # Use rotating user agents
    try:
        ua = UserAgent()
        user_agent = ua.random
    except Exception:
        # Fallback if fake_useragent fails
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        user_agent = random.choice(user_agents)
    
    options.add_argument(f"user-agent={user_agent}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Anti-detection measures via JavaScript
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """)
        driver.execute_script("""
        window.navigator.chrome = { runtime: {} };
        window.navigator.languages = ['en-US', 'en'];
        """)
        
        return driver
    except Exception as e:
        logger.error(f"Error creating WebDriver: {e}")
        raise

def safe_get_url(driver, url, retry_count=3):
    """Safely navigate to a URL with retry logic and CAPTCHA detection."""
    for attempt in range(retry_count):
        try:
            driver.get(url)
            human_like_delay(3, 6)
            
            # Check for CAPTCHA
            if check_for_captcha(driver):
                logger.warning(f"CAPTCHA detected on attempt {attempt+1}!")
                
                if not driver.execute_script("return document.querySelector('iframe[title*=recaptcha]')"):
                    # If no recaptcha iframe, it might be a block page
                    logger.error("Google Scholar is blocking access. Consider using a different IP or waiting.")
                    return False
                else:
                    logger.warning("CAPTCHA challenge present, waiting for manual intervention...")
                    # If in visible mode, give user time to solve CAPTCHA
                    time.sleep(30)  # 30 seconds to solve CAPTCHA
                    if check_for_captcha(driver):
                        logger.error("CAPTCHA not solved, retrying...")
                        continue
                    else:
                        logger.info("CAPTCHA appears to be solved, continuing...")
                        return True
            
            # Simulate human-like reading behavior occasionally
            if random.random() < 0.3:
                scroll_page_gradually(driver)
            
            return True
            
        except WebDriverException as e:
            logger.warning(f"Error navigating to {url} on attempt {attempt+1}: {e}")
            human_like_delay(5, 10)  # Longer delay between retries
    
    logger.error(f"Failed to load {url} after {retry_count} attempts")
    return False