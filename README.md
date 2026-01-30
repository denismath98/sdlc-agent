# WordCount CLI Tool

A simple command‑line utility to count words, lines, or characters in a text file.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m src.wordcount --file path/to/file.txt --mode words
python -m src.wordcount --file path/to/file.txt --mode lines
python -m src.wordcount --file path/to/file.txt --mode chars
```

## Running Tests

```bash
pytest
```
