"""Tests for the Google Scholar citation analyzer."""

import unittest
from unittest.mock import patch, MagicMock
from scholar_citations.parsers import extract_authors, similar_authors, has_author_overlap

class TestParsers(unittest.TestCase):
    """Test cases for parsing functions."""
    
    def test_extract_authors(self):
        """Test extraction of author names."""
        self.assertEqual(extract_authors("J Smith, A Jones"), ["j smith", "a jones"])
        self.assertEqual(extract_authors("Smith JS, Jones A et al."), ["smith js", "jones a"])
        
    def test_similar_authors(self):
        """Test author name similarity detection."""
        self.assertTrue(similar_authors("j smith", "j smith"))
        self.assertTrue(similar_authors("john smith", "smith"))
        self.assertTrue(similar_authors("j smith", "john smith"))
        self.assertFalse(similar_authors("j smith", "a jones"))
        
    def test_author_overlap(self):
        """Test detection of overlapping authors."""
        self.assertTrue(has_author_overlap(["j smith", "a jones"], ["j smith", "b brown"]))
        self.assertFalse(has_author_overlap(["j smith", "a jones"], ["c doe", "b brown"]))

# More test cases...