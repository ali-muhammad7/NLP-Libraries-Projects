# Stanza – NLP Forensics Lab

An interactive NLP desktop application built with Python, Tkinter, and Stanza. It analyzes text and presents linguistic information through an interactive forensic-style dashboard.

## Features
- Tokenization and word analysis.
- Part-of-Speech (POS) tagging.
- Lemmatization.
- Dependency parsing.
- Named Entity Recognition (NER).
- Interactive token evidence board.
- View detailed information about individual tokens.
- Display token, entity, and relation counts.

## Technologies
- Python
- Stanza
- Tkinter

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

**Note:** On the first run, Stanza downloads the required English language model. An internet connection is required for this initial download.

The current implementation analyzes the first sentence returned by Stanza.

**Author:** Ali Muhammad
