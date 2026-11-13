# VADER Signal Desk

A beginner-friendly sentiment analysis desktop application built with Python, Tkinter, and NLTK's VADER. It features a retro audio mixing console interface with visual sentiment meters.

## Features
- Analyze positive, negative, and neutral sentiment.
- Display the VADER compound score.
- Visual sentiment gauges with needle indicators.
- Analyze sentiment sentence by sentence.
- LED indicators for sentiment levels.
- Clear input and reset results.

## Technologies
- Python
- NLTK
- VADER Sentiment Analyzer
- Tkinter

## Installation

```bash
pip install -r requirements.txt
```

Download the required NLTK resources:

```python
import nltk

nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('punkt_tab')
```

## Run

```bash
python main.py
```

**Author:** Ali Muhammad
