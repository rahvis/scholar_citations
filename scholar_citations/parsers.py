"""Functions for parsing Google Scholar content."""

import re

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
    
    # Split names into words
    words1 = author1.split()
    words2 = author2.split()
    
    # Check if one name is just the last name of the other
    if len(words1) > 1 and len(words2) == 1:
        if words1[-1] == words2[0]:  # Last name of author1 matches the single name of author2
            return True
    elif len(words2) > 1 and len(words1) == 1:
        if words2[-1] == words1[0]:  # Last name of author2 matches the single name of author1
            return True
    
    # Check if last names match
    if words1 and words2 and words1[-1] == words2[-1]:
        # Check initials if present
        if len(words1) > 1 and len(words2) > 1:
            # Compare first initials
            if words1[0][0] == words2[0][0]:
                return True
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