# Scholar Citations

A tool for analyzing self-citations in Google Scholar profiles.

## Installation

```
pip install scholar-citations
```
Or with conda:
```
conda install -c conda-forge scholar-citations
```

## Usage

```
scholar-citations https://scholar.google.com/citations?user=USER_ID
```

### Options

- `--max-papers`: Maximum number of papers to analyze
- `--max-citations`: Maximum number of citations to check per paper
- `--output`: Output file for detailed results (JSON)
- `--visible`: Show browser window during analysis
- `--debug`: Enable debug logging

## License

MIT