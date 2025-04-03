"""Utility functions."""

import logging
import random
import re
import time

logger = logging.getLogger(__name__)

def human_like_delay(min_seconds=2, max_seconds=5):
    """Add a random delay with non-uniform distribution to mimic human behavior."""
    # Non-uniform distribution - more weight to middle values, less to extremes
    delay = min_seconds + (max_seconds - min_seconds) * (0.5 + 0.5 * (random.random() - 0.5))
    time.sleep(delay)

def scroll_page_gradually(driver):
    """Scroll the page gradually to mimic human reading behavior."""
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    current_position = 0
    
    while current_position < total_height:
        # Random scroll distance
        scroll_distance = random.randint(100, viewport_height // 2)
        current_position += scroll_distance
        
        # Scroll with a smooth behavior
        driver.execute_script(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}})")
        
        # Random pause after scrolling
        time.sleep(random.uniform(0.5, 2.0))
        
        # Sometimes pause longer as if reading
        if random.random() < 0.2:
            time.sleep(random.uniform(2.0, 4.0))

# Other utility functions...