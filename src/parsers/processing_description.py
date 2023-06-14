import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer


nltk.download('stopwords')
nltk.download('punkt')
unique_stops = set(stopwords.words('russian'))
symbols = [".", "-", ",", ";", "(", "!", "?", ")", "«", "»", ":"]


def processing_description(text):
    tokens = word_tokenize(text)
    no_stops = []
    for token in tokens:
        token = token.lower()
        if "/" in token:
            no_stops.append(token[:token.find("/")])
            no_stops.append(token[token.find("/") + 1:])
            continue
        if "-" in token:
            if token[:token.find("-")]:
                no_stops.append(token[:token.find("-")])
            if token[token.find("-") + 1:]:
                no_stops.append(token[token.find("-") + 1:])
            continue
        if token not in unique_stops and token not in symbols:
            no_stops.append(token)
    morph = MorphAnalyzer()
    lemmatized = []
    for token in no_stops:
        token = morph.normal_forms(token)[0]
        lemmatized.append(token)
    string = ""
    for element in lemmatized:
        string = string + " " + element
    return string
