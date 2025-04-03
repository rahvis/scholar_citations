#!/usr/bin/env python
#pypi-AgEIcHlwaS5vcmcCJGRmYzgwMmM4LWQzOTYtNDM1MS04Y2E5LTU4OGFmNmMzY2ViYgACKlszLCJhOGQwN2QwMC1iMzQ0LTQ3MmItOTJkMi05NjQzYjAwZWM5YWQiXQAABiBm4TFbWkg8jPpRJX8e3HaOWo5_kJvzK_GX-Z8_S46F6A
from setuptools import setup, find_packages

setup(
    name="scholar_citations",
    version="0.1.0",
    description="Google Scholar self-citation analyzer",
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