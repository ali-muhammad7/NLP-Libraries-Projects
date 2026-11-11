# NLP Toolkit – NLTK

A beginner-friendly desktop application built with Python, Tkinter, and NLTK to explore fundamental Natural Language Processing (NLP) operations through a graphical user interface.

## Features

This application provides 8 NLP operations:

1. **Tokenization** – Splits text into sentences and words.
2. **Sentence Tokenization** – Separates text into individual sentences.
3. **Word Tokenization** – Breaks text into individual words.
4. **Stopword Removal** – Removes common English words such as "the", "is", and "a".
5. **Stemming** – Reduces words to their root forms using Porter Stemmer.
6. **Lemmatization** – Converts words into dictionary base forms using WordNet.
7. **POS Tagging** – Identifies grammatical roles such as nouns, verbs, and adjectives.
8. **Frequency Distribution** – Counts word occurrences and displays their frequency.

## Technologies Used

- Python
- NLTK (Natural Language Toolkit)
- Tkinter
- Porter Stemmer
- WordNet Lemmatizer

## Project Structure

```text
NLTK_Project/
├── main.py
├── download_data.py
├── requirements.txt
├── text for nltk.txt
└── README.md
```

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/ali-muhammad7/NLP-Libraries-Projects.git
```

**2. Navigate to the project folder**

```bash
cd NLP-Libraries-Projects/NLTK_Project
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Download required NLTK datasets**

Run the following Python commands once:

```python
import nltk

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
```

## Run the Application

```bash
python main.py
```

## How to Use

1. Launch the application.
2. Enter your text in the input box.
3. Select an NLP operation from the right-side panel.
4. View the processed results in the output section.
5. Use Clear to reset the input and output fields.

## Learning Objectives

- Understand fundamental NLP preprocessing techniques.
- Explore tokenization, stemming, and lemmatization.
- Learn how POS tagging works.
- Analyze word frequency in text.
- Build a desktop GUI application using Tkinter.

## Author

**Ali Muhammad**

BS Artificial Intelligence Student | Aspiring AI Engineer

GitHub: [@ali-muhammad7](https://github.com/ali-muhammad7)

---

*Built as part of my journey into Natural Language Processing and Artificial Intelligence.*
