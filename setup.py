#!/usr/bin/env python3
"""
Setup script for NotebookLM Sanitizer
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="notebooklm-sanitizer",
    version="1.0.0",
    author="AquaBrain Engineering",
    author_email="info@aquabrain.io",
    description="Safe file sanitization and preparation for NotebookLM AI ingestion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ofer2300/NotebookLM_Sanitizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only stdlib
    ],
    entry_points={
        "console_scripts": [
            "sanitizer=sanitizer:main",
            "nbsanitize=sanitizer:main",
        ],
    },
    include_package_data=True,
    keywords="notebooklm, ai, document, sanitizer, preprocessing, construction",
)
