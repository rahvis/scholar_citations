"""Core analysis functions for Google Scholar citations."""

import logging
import time
import json
from .driver import (
    create_stealth_driver, 
    safe_get_url, 
    human_like_delay
)
from .parsers import extract_authors, has_author_overlap

logger = logging.getLogger(__name__)

def get_author_details(driver, profile_url):
    """Get basic details about the author."""
    if not safe_get_url(driver, profile_url):
        return {'name': 'Unknown'}
    
    try:
        # Wait for profile to load
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import NoSuchElementException
        
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
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        
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
    import re
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
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
            from .driver import check_for_captcha
            
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
    import random
    
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