# Scholar Citations

A Python tool for analyzing self-citation patterns in Google Scholar profiles.

[![Buy Me A Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&slug=visrah&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/visrah)


## Overview

Scholar Citations is a powerful tool that helps researchers and evaluators analyze self-citation patterns in Google Scholar profiles. Self-citations (when authors cite their own previous work) are a normal part of academic publishing, but excessive self-citation can sometimes skew metrics like h-index and citation counts.

This tool allows you to:
- Analyze any Google Scholar profile to identify self-citations
- Calculate self-citation percentages and metrics
- Generate detailed reports of self-citation patterns
- Estimate self-citation counts for highly-cited papers using sampling

### Problems noted in Nature 572, 578-579 (2019)
```bash
doi: https://doi.org/10.1038/d41586-019-02479-7
```
Vaidyanathan, a computer scientist at the Vel Tech R&D Institute of Technology, a privately run institute, is an extreme example: he has received 94% of his citations from himself or his co- authors up to 2017, according to a study in PLoS Biology this month. 

https://github.com/rahvis/scholar_citations/blob/main/notes/vannoorden2019.pdf

## Installation

```bash
pip install scholar-citations
```

## Requirements

- Python 3.7 or higher
- Google Chrome browser (for Selenium automation)

## Usage

### Basic Usage

```bash
scholar-citations "https://scholar.google.com/citations?user=USER_ID"
```

Replace `USER_ID` with the ID from the Google Scholar profile URL you want to analyze.

### Advanced Options

```bash
# Analyze only the first 20 papers
scholar-citations "https://scholar.google.com/citations?user=USER_ID" --max-papers 20

# Check only 10 citations per paper (for faster analysis)
scholar-citations "https://scholar.google.com/citations?user=USER_ID" --max-citations 10

# Save detailed results to a JSON file
scholar-citations "https://scholar.google.com/citations?user=USER_ID" --output results.json

# Show the browser window (useful for solving CAPTCHAs)
scholar-citations "https://scholar.google.com/citations?user=USER_ID" --visible

# Enable debug logging
scholar-citations "https://scholar.google.com/citations?user=USER_ID" --debug
```

## Command Help

```bash
scholar-citations --help                                           
usage: scholar-citations [-h] [--max-papers MAX_PAPERS] [--max-citations MAX_CITATIONS] [--output OUTPUT] [--visible] [--debug] url

Analyze self-citations on Google Scholar

positional arguments:
  url                   Google Scholar profile URL

optional arguments:
  -h, --help            show this help message and exit
  --max-papers MAX_PAPERS
                        Maximum number of papers to analyze
  --max-citations MAX_CITATIONS
                        Maximum number of citations to check per paper
  --output OUTPUT       Output file for detailed results (JSON)
  --visible             Show browser window during analysis
  --debug               Enable debug logging
```

## Features

- **Anti-detection measures**: Uses sophisticated browser fingerprinting techniques to avoid detection
- **Robust author matching**: Intelligently matches different formats of author names to detect self-citations
- **Progress saving**: Saves intermediate results to avoid losing progress if the process is interrupted
- **Sampling**: For papers with many citations, examines a representative sample and extrapolates results
- **Detailed reporting**: Provides both summary statistics and detailed paper-by-paper analysis
- **CAPTCHA handling**: When run with `--visible`, allows you to solve CAPTCHAs if they appear

## Example Output

```
======= RESULTS =======
Author: Author XYZ
Papers analyzed: 101 of 101
Total citations: 129
Self-citations: 21
Self-citation percentage: 16.28%
```

## How It Works

1. The tool visits the specified Google Scholar profile
2. It extracts the list of publications by the author
3. For each publication, it analyzes the "Cited by" list
4. It compares author lists to identify overlaps (self-citations)
5. It calculates statistics and generates a report

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/scholar_citations.git
cd scholar_citations
pip install -e .
```

### Running Tests

```bash
pip install pytest
pytest tests/
================================================================== test session starts ==================================================================
platform darwin -- Python 3.9.21, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/rahul/Downloads/scholar_citations
configfile: pyproject.toml
plugins: cov-6.0.0
collected 3 items                                                                                                                                       

tests/test_analyzer.py ...                                                                                                                        [100%]

=================================================================== 3 passed in 0.03s ===================================================================
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this tool in your research, please cite it as:

```
Vishwakarma, R. (2025). Scholar Citations: A tool for analyzing self-citation patterns in Google Scholar profiles. [Software]. Available from https://pypi.org/project/scholar-citations/
```

## Disclaimer

This tool is meant for academic and research purposes only. Please use responsibly and respect Google Scholar's terms of service. The tool includes rate limiting and anti-detection features to minimize impact on Google's servers.
