#!/usr/bin/env python
#pypi-AgEIcHlwaS5vcmcCJGUwZTYwYzQ1LWI4ZTUtNGNmMi1hZDZjLTcwNmE5ODE5ZTIwNAACKlszLCJhOGQwN2QwMC1iMzQ0LTQ3MmItOTJkMi05NjQzYjAwZWM5YWQiXQAABiAQycVCXPeVYZ-0bL0YMUjnbCwmbSb27_WGPzFmXWXKKw
 
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README.md file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="scholar_citations",
    version="0.1.3",
    description="Google Scholar self-citation analyzer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rahul Vishwakarma",
    author_email="rahul_vishwakarma@icloud.com",
    url="https://github.com/rahvis/scholar_citations",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "scholar-citations=scholar_citations.cli:main",
        ],
    },
    python_requires=">=3.7",
    install_requires=[
        "selenium",
        "webdriver-manager",
        "fake-useragent",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)