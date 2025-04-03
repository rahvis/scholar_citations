import argparse
import time
import random
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    """Set up and return a Chrome WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # Use a realistic user agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def random_delay(min_seconds=2, max_seconds=5):
    """Add a random delay to avoid detection."""
    time.sleep(min_seconds + random.random() * (max_seconds - min_seconds))

def extract_authors(author_string):
    """Extract and normalize author names from a string."""
    if not author_string:
        return []
    
    # Handle "et al." format
    if " et al." in author_string:
        author_string = author_string.replace(" et al.", "")
    
    # Split by comma and normalize
    authors = []
    for author in author_string.split(','):
        # Remove affiliations in parentheses
        author = re.sub(r'\([^)]*\)', '', author)
        author = author.strip().lower()
        if author:
            authors.append(author)
    
    return authors

def has_author_overlap(authors1, authors2):
    """Check if there is any overlap between two lists of author names."""
    for a1 in authors1:
        for a2 in authors2:
            # Check if names match (exact or partial)
            if a1 == a2 or (len(a1) > 3 and a1 in a2) or (len(a2) > 3 and a2 in a1):
                return True
    return False

def get_author_details(driver, profile_url):
    """Get basic details about the author."""
    driver.get(profile_url)
    random_delay()
    
    try:
        # Wait for profile to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "gsc_prf_in"))
        )
        
        author_name = driver.find_element(By.ID, "gsc_prf_in").text
        return {'name': author_name}
    
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error getting author details: {e}")
        return {'name': 'Unknown'}

def get_publications(driver, profile_url, max_papers=None):
    """Get the list of publications for an author."""
    driver.get(profile_url)
    random_delay()
    
    try:
        # Wait for publications to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gsc_a_tr"))
        )
        
        # Click "Show more" until all papers are loaded or max_papers is reached
        while True:
            paper_rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
            
            if max_papers and len(paper_rows) >= max_papers:
                break
            
            try:
                show_more_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "gsc_bpf_more"))
                )
                show_more_button.click()
                random_delay(1, 3)
            except TimeoutException:
                # No more "Show more" button
                break
        
        # Get all paper rows
        paper_rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
        if max_papers:
            paper_rows = paper_rows[:max_papers]
        
        publications = []
        for paper_row in paper_rows:
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
                
                publications.append({
                    'title': title,
                    'url': paper_url,
                    'authors': authors,
                    'author_list': extract_authors(authors),
                    'citation_count': citation_count,
                    'citation_url': citation_url
                })
            
            except Exception as e:
                print(f"Error extracting publication details: {e}")
                continue
        
        return publications
    
    except Exception as e:
        print(f"Error getting publications: {e}")
        return []

def get_citations(driver, citation_url, max_citations=None):
    """Get the list of papers that cite a specific publication."""
    if not citation_url:
        return []
    
    driver.get(citation_url)
    random_delay()
    
    try:
        # Wait for citations to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "gs_ri"))
        )
        
        # Get citation elements
        citation_elements = driver.find_elements(By.CLASS_NAME, "gs_ri")
        
        # Limit if max_citations specified
        if max_citations:
            citation_elements = citation_elements[:max_citations]
        
        citations = []
        for citation_element in citation_elements:
            try:
                # Get title
                title_element = citation_element.find_element(By.CLASS_NAME, "gs_rt")
                title = title_element.text
                # Clean up title (remove [PDF], [HTML], etc.)
                title = re.sub(r'\[[^\]]+\]', '', title).strip()
                
                # Get authors and publication info
                info_element = citation_element.find_element(By.CLASS_NAME, "gs_a")
                info_text = info_element.text
                
                # Extract just the author part (before first dash)
                authors = info_text.split('-')[0].strip()
                
                citations.append({
                    'title': title,
                    'authors': authors,
                    'author_list': extract_authors(authors)
                })
            
            except Exception as e:
                print(f"Error extracting citation details: {e}")
                continue
        
        return citations
    
    except Exception as e:
        print(f"Error getting citations: {e}")
        return []

def analyze_self_citations(profile_url, max_papers=None, max_citations_per_paper=None, headless=True):
    """Analyze self-citations for a Google Scholar profile."""
    driver = setup_driver(headless)
    
    try:
        print("Getting author details...")
        author = get_author_details(driver, profile_url)
        
        print(f"Getting publications for {author['name']}...")
        publications = get_publications(driver, profile_url, max_papers)
        
        if not publications:
            print("No publications found.")
            return {
                'author': author['name'],
                'total_papers': 0,
                'analyzed_papers': 0,
                'total_citations': 0,
                'self_citations': 0,
                'self_citation_percentage': 0,
                'self_citation_details': []
            }
        
        print(f"Found {len(publications)} publications.")
        
        total_citations = 0
        self_citations = 0
        self_citation_details = []
        
        for i, pub in enumerate(publications, 1):
            print(f"[{i}/{len(publications)}] Analyzing: {pub['title'][:50]}{'...' if len(pub['title']) > 50 else ''}")
            
            if pub['citation_count'] > 0 and pub['citation_url']:
                total_citations += pub['citation_count']
                
                citations_to_check = min(pub['citation_count'], max_citations_per_paper) if max_citations_per_paper else pub['citation_count']
                print(f"  Checking {citations_to_check} of {pub['citation_count']} citations...")
                
                citations = get_citations(driver, pub['citation_url'], max_citations_per_paper)
                
                pub_self_citations = 0
                for citation in citations:
                    if has_author_overlap(pub['author_list'], citation['author_list']):
                        self_citations += 1
                        pub_self_citations += 1
                        
                        self_citation_details.append({
                            'original_paper': pub['title'],
                            'citing_paper': citation['title'],
                            'original_authors': pub['authors'],
                            'citing_authors': citation['authors']
                        })
                
                print(f"  Found {pub_self_citations} self-citations.")
            else:
                print("  No citations to analyze.")
        
        # Calculate results
        self_citation_percentage = (self_citations / total_citations * 100) if total_citations > 0 else 0
        
        return {
            'author': author['name'],
            'total_papers': len(publications),
            'analyzed_papers': len(publications),
            'total_citations': total_citations,
            'self_citations': self_citations,
            'self_citation_percentage': self_citation_percentage,
            'self_citation_details': self_citation_details
        }
    
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Analyze self-citations on Google Scholar')
    parser.add_argument('url', help='Google Scholar profile URL')
    parser.add_argument('--max-papers', type=int, default=None, help='Maximum number of papers to analyze')
    parser.add_argument('--max-citations', type=int, default=None, help='Maximum number of citations to check per paper')
    parser.add_argument('--output', type=str, default=None, help='Output file for detailed results (JSON)')
    parser.add_argument('--visible', action='store_true', help='Show browser window during analysis')
    args = parser.parse_args()
    
    try:
        print(f"Starting analysis of: {args.url}")
        if args.max_papers:
            print(f"Limiting to {args.max_papers} papers")
        if args.max_citations:
            print(f"Limiting to {args.max_citations} citations per paper")
        
        results = analyze_self_citations(
            args.url, 
            max_papers=args.max_papers, 
            max_citations_per_paper=args.max_citations,
            headless=not args.visible
        )
        
        print("\n======= RESULTS =======")
        print(f"Author: {results['author']}")
        print(f"Papers analyzed: {results['analyzed_papers']}")
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
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()