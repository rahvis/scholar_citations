import argparse
import time
import random
import json
import re
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("scholar_scraper.log"),
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)

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
    
    # Use rotating user agents to appear more human-like
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
    
    # Add proxy if available (uncomment and configure if needed)
    # if proxy:
    #     options.add_argument(f'--proxy-server={proxy}')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Additional anti-detection measures via JavaScript
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set additional navigator properties to mask automation
        driver.execute_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """)
        
        # Add human-like cookies and fingerprinting
        driver.execute_script("""
        window.navigator.chrome = { runtime: {} };
        window.navigator.languages = ['en-US', 'en'];
        """)
        
        return driver
    except Exception as e:
        logger.error(f"Error creating WebDriver: {e}")
        raise

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

def extract_authors(author_string):
    """Extract and normalize author names from a string."""
    if not author_string:
        return []
    
    # Process "et al." format
    author_string = re.sub(r'\s+et al\.?', '', author_string)
    
    # Split by comma and normalize
    authors = []
    for author in author_string.split(','):
        # Remove affiliations in parentheses
        author = re.sub(r'\([^)]*\)', '', author)
        author = author.strip().lower()
        
        # Skip empty strings
        if not author:
            continue
            
        # Handle initials (e.g., "J.S. Smith" -> "j s smith")
        author = re.sub(r'([A-Z])\.', r'\1 ', author)
        
        # Normalize spacing and remove extra whitespace
        author = re.sub(r'\s+', ' ', author)
        
        authors.append(author)
    
    return authors

def similar_authors(author1, author2, threshold=0.7):
    """Check if two author names are similar using more sophisticated matching."""
    # Direct match
    if author1 == author2:
        return True
    
    # Check for subset (last name only vs. full name)
    words1 = author1.split()
    words2 = author2.split()
    
    # Check if last names match
    if words1 and words2 and words1[-1] == words2[-1]:
        # Check initials if present
        if len(words1) > 1 and len(words2) > 1:
            # Compare first initials
            if words1[0][0] == words2[0][0]:
                return True
    
    # For more complex cases, we could implement fuzzy matching here
    # but it would require additional libraries like fuzzywuzzy
    
    return False

def has_author_overlap(authors1, authors2):
    """Check if there is any overlap between two lists of author names."""
    if not authors1 or not authors2:
        return False
        
    for a1 in authors1:
        for a2 in authors2:
            if similar_authors(a1, a2):
                return True
    
    return False

def get_author_details(driver, profile_url):
    """Get basic details about the author."""
    if not safe_get_url(driver, profile_url):
        return {'name': 'Unknown'}
    
    try:
        # Wait for profile to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "gsc_prf_in"))
        )
        
        author_name = driver.find_element(By.ID, "gsc_prf_in").text
        
        # Try to get additional details if available
        details = {'name': author_name}
        
        try:
            affiliation = driver.find_element(By.CSS_SELECTOR, ".gsc_prf_il").text
            details['affiliation'] = affiliation
        except NoSuchElementException:
            pass
            
        return details
    
    except Exception as e:
        logger.error(f"Error getting author details: {e}")
        return {'name': 'Unknown'}

def get_publications(driver, profile_url, max_papers=None):
    """Get the list of publications for an author."""
    publications = []
    
    if not safe_get_url(driver, profile_url):
        return publications
    
    try:
        # Wait for publications to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gsc_a_tr"))
        )
        
        # Click "Show more" until all papers are loaded or max_papers is reached
        while True:
            # Get current paper rows
            paper_rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
            
            if max_papers and len(paper_rows) >= max_papers:
                # Enough papers loaded
                break
                
            try:
                # Try to find the "Show more" button with increased wait time
                show_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "gsc_bpf_more"))
                )
                
                # Check if button is disabled
                if "disabled" in show_more_button.get_attribute("class"):
                    logger.info("Show more button is disabled, all papers loaded")
                    break
                
                # Scroll to button and click with human-like behavior
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                human_like_delay(1, 2)
                show_more_button.click()
                human_like_delay(2, 5)
                
            except TimeoutException:
                # No more "Show more" button or it's not clickable
                logger.info("No more papers to load or show more button not found")
                break
        
        # Get all paper rows after loading
        paper_rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
        if max_papers:
            paper_rows = paper_rows[:max_papers]
        
        logger.info(f"Processing {len(paper_rows)} publications")
        
        for i, paper_row in enumerate(paper_rows):
            try:
                # Get paper title and link
                title_element = paper_row.find_element(By.CLASS_NAME, "gsc_a_at")
                title = title_element.text
                paper_url = title_element.get_attribute("href")
                
                # Get authors (first gs_gray element)
                authors_element = paper_row.find_elements(By.CLASS_NAME, "gs_gray")[0]
                authors = authors_element.text
                
                # Get citation count and URL
                citation_element = paper_row.find_element(By.CLASS_NAME, "gsc_a_ac")
                citation_text = citation_element.text.strip()
                citation_count = int(citation_text) if citation_text.isdigit() else 0
                citation_url = citation_element.get_attribute("href") if citation_count > 0 else None
                
                # Get venue/journal (second gs_gray element)
                venue_element = paper_row.find_elements(By.CLASS_NAME, "gs_gray")[1]
                venue = venue_element.text
                
                # Get year (optional)
                year = None
                try:
                    year_element = paper_row.find_element(By.CLASS_NAME, "gsc_a_h")
                    year_text = year_element.text.strip()
                    if year_text.isdigit():
                        year = int(year_text)
                except NoSuchElementException:
                    pass
                
                publications.append({
                    'title': title,
                    'url': paper_url,
                    'authors': authors,
                    'author_list': extract_authors(authors),
                    'citation_count': citation_count,
                    'citation_url': citation_url,
                    'venue': venue,
                    'year': year,
                    'index': i + 1
                })
                
                # Occasionally introduce variation in processing time
                if random.random() < 0.2:
                    human_like_delay(0.5, 1.5)
            
            except Exception as e:
                logger.error(f"Error extracting publication #{i+1}: {e}")
                continue
        
        return publications
    
    except Exception as e:
        logger.error(f"Error getting publications: {e}")
        return []

def get_citations(driver, citation_url, original_authors, max_citations=None, retries=2):
    """Get the list of papers that cite a specific publication."""
    if not citation_url:
        return []
    
    citations = []
    page_num = 0
    total_citations = 0
    
    while True:
        # Construct URL with page parameter if not the first page
        current_url = citation_url
        if page_num > 0:
            if "start=" in citation_url:
                # Replace existing start parameter
                current_url = re.sub(r'start=\d+', f'start={page_num*10}', citation_url)
            else:
                # Add start parameter
                if "?" in citation_url:
                    current_url = f"{citation_url}&start={page_num*10}"
                else:
                    current_url = f"{citation_url}?start={page_num*10}"
        
        if not safe_get_url(driver, current_url):
            if retries > 0:
                logger.warning(f"Retrying citation page, {retries} attempts left")
                human_like_delay(10, 20)  # Longer delay before retry
                return get_citations(driver, citation_url, original_authors, max_citations, retries-1)
            else:
                logger.error("Failed to load citation page after retries")
                return citations
        
        try:
            # Check if page loaded properly
            if check_for_captcha(driver):
                logger.warning("CAPTCHA detected on citation page")
                if retries > 0:
                    human_like_delay(15, 30)
                    return get_citations(driver, citation_url, original_authors, max_citations, retries-1)
                else:
                    return citations
            
            # Wait for citations to load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "gs_ri"))
                )
            except TimeoutException:
                # Check if it's actually empty results
                if "no citations were found" in driver.page_source.lower() or driver.find_elements(By.ID, "gs_ccl_results") and not driver.find_elements(By.CLASS_NAME, "gs_ri"):
                    logger.info("No citations found for this paper")
                    return citations
                else:
                    logger.warning("Timeout waiting for citation elements")
                    if retries > 0:
                        human_like_delay(5, 10)
                        return get_citations(driver, citation_url, original_authors, max_citations, retries-1)
                    else:
                        return citations
            
            # Get citation elements
            citation_elements = driver.find_elements(By.CLASS_NAME, "gs_ri")
            
            # Process citation elements
            for citation_element in citation_elements:
                try:
                    # Get title
                    title_element = citation_element.find_element(By.CLASS_NAME, "gs_rt")
                    title = title_element.text
                    # Clean up title (remove [PDF], [HTML], etc.)
                    title = re.sub(r'\[[^\]]+\]', '', title).strip()
                    
                    # Try to get URL
                    url = None
                    try:
                        link_element = title_element.find_element(By.TAG_NAME, "a")
                        url = link_element.get_attribute("href")
                    except NoSuchElementException:
                        pass
                    
                    # Get authors and publication info
                    info_element = citation_element.find_element(By.CLASS_NAME, "gs_a")
                    info_text = info_element.text
                    
                    # Extract just the author part (before first dash)
                    authors = info_text.split('-')[0].strip() if '-' in info_text else info_text
                    
                    # Extract year if available
                    year_match = re.search(r'\b(19|20)\d{2}\b', info_text)
                    year = int(year_match.group(0)) if year_match else None
                    
                    # Extract venue
                    venue_parts = info_text.split('-')
                    venue = venue_parts[1].strip() if len(venue_parts) > 1 else ""
                    
                    # Check for self-citation
                    citing_authors = extract_authors(authors)
                    is_self_citation = has_author_overlap(original_authors, citing_authors)
                    
                    citation_data = {
                        'title': title,
                        'url': url,
                        'authors': authors,
                        'author_list': citing_authors,
                        'year': year,
                        'venue': venue,
                        'is_self_citation': is_self_citation
                    }
                    
                    citations.append(citation_data)
                    total_citations += 1
                    
                    # Break if we've reached the max citations
                    if max_citations and total_citations >= max_citations:
                        return citations
                
                except Exception as e:
                    logger.error(f"Error extracting citation details: {e}")
                    continue
            
            # Check if there's a "Next" button for pagination
            next_button = None
            try:
                next_buttons = driver.find_elements(By.CSS_SELECTOR, ".gs_btnPR")
                for button in next_buttons:
                    if "Next" in button.get_attribute("innerHTML"):
                        next_button = button
                        break
            except NoSuchElementException:
                next_button = None
            
            # If no next button or no citations on this page, we're done
            if not next_button or not citation_elements:
                break
                
            # Move to next page
            page_num += 1
            
            # If we have enough citations, exit
            if max_citations and total_citations >= max_citations:
                break
                
            # Wait between page navigations (longer delay)
            human_like_delay(3, 7)
        
        except Exception as e:
            logger.error(f"Error processing citation page {page_num}: {e}")
            if retries > 0:
                return get_citations(driver, citation_url, original_authors, max_citations, retries-1)
            else:
                break
    
    return citations

def analyze_self_citations(profile_url, max_papers=None, max_citations_per_paper=None, visible=True, output_file=None):
    """Analyze self-citations for a Google Scholar profile."""
    driver = None
    results = {
        'author': {'name': 'Unknown'},
        'total_papers': 0,
        'analyzed_papers': 0,
        'total_citations': 0,
        'self_citations': 0,
        'self_citation_percentage': 0,
        'self_citation_details': []
    }
    
    try:
        logger.info(f"Starting analysis of: {profile_url}")
        logger.info(f"Settings: max_papers={max_papers}, max_citations_per_paper={max_citations_per_paper}")
        
        # Create a new driver with stealth settings
        driver = create_stealth_driver(headless=not visible)
        
        # Get author details
        logger.info("Getting author details...")
        author = get_author_details(driver, profile_url)
        results['author'] = author
        
        # Get publications
        logger.info(f"Getting publications for {author['name']}...")
        publications = get_publications(driver, profile_url, max_papers)
        
        if not publications:
            logger.warning("No publications found. Check if the profile is accessible.")
            return results
        
        results['total_papers'] = len(publications)
        results['analyzed_papers'] = len(publications)
        
        logger.info(f"Found {len(publications)} publications.")
        
        # Process citations and analyze self-citations
        total_citations = 0
        self_citations = 0
        self_citation_details = []
        
        for i, pub in enumerate(publications):
            logger.info(f"[{i+1}/{len(publications)}] Analyzing: {pub['title'][:50]}{'...' if len(pub['title']) > 50 else ''}")
            
            if pub['citation_count'] > 0 and pub['citation_url']:
                total_citations += pub['citation_count']
                
                citations_to_check = min(pub['citation_count'], max_citations_per_paper) if max_citations_per_paper else pub['citation_count']
                logger.info(f"  Checking up to {citations_to_check} of {pub['citation_count']} citations...")
                
                # Get citations for this publication
                citations = get_citations(driver, pub['citation_url'], pub['author_list'], max_citations_per_paper)
                
                # Count self-citations
                pub_self_citations = sum(1 for citation in citations if citation['is_self_citation'])
                
                # If we didn't check all citations, estimate the total self-citations
                if max_citations_per_paper and pub['citation_count'] > max_citations_per_paper:
                    # Calculate the ratio of self-citations in the sample
                    if citations:
                        self_cite_ratio = pub_self_citations / len(citations)
                        # Estimate total self-citations for this paper
                        estimated_self_cites = round(self_cite_ratio * pub['citation_count'])
                        logger.info(f"  Found {pub_self_citations} self-citations in sample. Estimated total: {estimated_self_cites}")
                        self_citations += estimated_self_cites
                    else:
                        logger.warning("  No citations retrieved for estimation")
                else:
                    # We checked all citations
                    logger.info(f"  Found {pub_self_citations} self-citations.")
                    self_citations += pub_self_citations
                
                # Collect details for self-citations
                for citation in citations:
                    if citation['is_self_citation']:
                        self_citation_details.append({
                            'paper_index': pub['index'],
                            'original_paper': pub['title'],
                            'original_authors': pub['authors'],
                            'original_year': pub['year'],
                            'citing_paper': citation['title'],
                            'citing_authors': citation['authors'],
                            'citing_year': citation['year']
                        })
            else:
                logger.info("  No citations to analyze.")
            
            # Save intermediate results to avoid losing progress in case of errors
            if output_file and i % 5 == 0:
                intermediate_results = {
                    'author': results['author'],
                    'total_papers': len(publications),
                    'analyzed_papers': i + 1,
                    'total_citations': total_citations,
                    'self_citations': self_citations,
                    'self_citation_percentage': (self_citations / total_citations * 100) if total_citations > 0 else 0,
                    'self_citation_details': self_citation_details,
                    'status': 'in_progress',
                    'last_updated': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open(f"{output_file}.partial", 'w', encoding='utf-8') as f:
                    json.dump(intermediate_results, f, indent=2)
        
        # Calculate final results
        results['total_citations'] = total_citations
        results['self_citations'] = self_citations
        results['self_citation_percentage'] = (self_citations / total_citations * 100) if total_citations > 0 else 0
        results['self_citation_details'] = self_citation_details
        
        return results
    
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return results
    
    finally:
        if driver:
            driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Analyze self-citations on Google Scholar with stealth browsing')
    parser.add_argument('url', help='Google Scholar profile URL')
    parser.add_argument('--max-papers', type=int, default=None, help='Maximum number of papers to analyze')
    parser.add_argument('--max-citations', type=int, default=None, help='Maximum number of citations to check per paper')
    parser.add_argument('--output', type=str, default=None, help='Output file for detailed results (JSON)')
    parser.add_argument('--visible', action='store_true', help='Show browser window during analysis (recommended for CAPTCHA solving)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Start the analysis
    try:
        results = analyze_self_citations(
            args.url, 
            max_papers=args.max_papers, 
            max_citations_per_paper=args.max_citations,
            visible=args.visible,
            output_file=args.output
        )
        
        # Print results summary
        print("\n======= RESULTS =======")
        print(f"Author: {results['author']['name']}")
        print(f"Papers analyzed: {results['analyzed_papers']} of {results['total_papers']}")
        print(f"Total citations: {results['total_citations']}")
        print(f"Self-citations: {results['self_citations']}")
        print(f"Self-citation percentage: {results['self_citation_percentage']:.2f}%")
        
        if results['self_citation_details']:
            print("\nSelf-citation examples (first 5):")
            for i, citation in enumerate(results['self_citation_details'][:5], 1):
                print(f"{i}. Original: {citation['original_paper'][:50]}{'...' if len(citation['original_paper']) > 50 else ''}")
                print(f"   Citing: {citation['citing_paper'][:50]}{'...' if len(citation['citing_paper']) > 50 else ''}")
            
            if len(results['self_citation_details']) > 5:
                print(f"\n... and {len(results['self_citation_details']) - 5} more self-citations")
        
        # Save detailed results if output file specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")
    
    except Exception as e:
        print(f"\nCritical error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()