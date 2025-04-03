"""General utility functions."""

import logging
import json
import time

logger = logging.getLogger(__name__)

def save_interim_results(results, output_file):
    """Save intermediate results to avoid losing progress."""
    if not output_file:
        return
        
    with open(f"{output_file}.partial", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved interim results to {output_file}.partial")