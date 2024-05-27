from setuptools import setup

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="scoreganizer-client-lib",
    description="Library for building clients for Scoreganizer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    author="Thomas Kolar",
    author_email="thomaskolar90@gmail.com",
    url="https://github.com/ralokt/scoreganizer-client-lib/",
    packages=["scoreganizer_client_lib"],
    platforms=["all"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Other Audience",
        "Topic :: Games/Entertainment :: Puzzle Games",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "minesweeper",
        "scoreganizer",
    ],
    install_requires=[
        "requests>=2.32.0",
    ],
)
