# WordCount CLI Tool

A simple command‑line utility to count words, lines, or characters in a text file.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m src.wordcount --file path/to/file.txt --mode words
```

Replace `words` with `lines` or `chars` to count lines or characters respectively.

## Example

```bash
$ echo -e "Hello world\nPython" > example.txt
$ python -m src.wordcount --file example.txt --mode words
3
$ python -m src.wordcount --file example.txt --mode lines
2
$ python -m src.wordcount --file example.txt --mode chars
24
```
