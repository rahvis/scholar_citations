"""Command-line interface for Google Scholar citation analyzer."""

import argparse
import logging
import traceback
import json
import sys
from .analyzer import analyze_self_citations

def setup_logging(debug=False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("scholar_scraper.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Entry point for the command-line interface."""
    parser = argparse.ArgumentParser(description='Analyze self-citations on Google Scholar')
    parser.add_argument('url', help='Google Scholar profile URL')
    parser.add_argument('--max-papers', type=int, default=None, help='Maximum number of papers to analyze')
    parser.add_argument('--max-citations', type=int, default=None, help='Maximum number of citations to check per paper')
    parser.add_argument('--output', type=str, default=None, help='Output file for detailed results (JSON)')
    parser.add_argument('--visible', action='store_true', help='Show browser window during analysis')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    setup_logging(args.debug)
    
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
        
        # Display examples of self-citations
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
        
        return 0
    except Exception as e:
        print(f"\nCritical error during analysis: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())