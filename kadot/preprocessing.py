from .tokenizers import RegexTokenizer
from .fuzzy import most_similar
from collections import defaultdict
from numpy import log, mean


class SpellingCorrector(object):
    """A simple spell checker"""

    def __init__(self, tokenizer=RegexTokenizer()):
        self.tokenizer = tokenizer
        self.words = set()

    def fit(self, documents):
        for document in documents:
            self.words.update(self.tokenizer.tokenize(document))
            self.words.update(self.tokenizer.tokenize(document.lower()))  # Add a lowercase version of the vocabulary

    def fit_from_file(self, filename):
        with open(filename) as document_file:
            self.fit([document_file.read()])

    def predict(self, documents):
        new_documents = []

        for document in documents:
            document = self.tokenizer.tokenize(document)
            corrected_document = document.copy()

            for word_position, word in enumerate(document):
                if word not in self.words:
                    corrected_document[word_position] = most_similar(word, self.words)[0][0]

            new_documents.append(self.tokenizer.rebuild_last(corrected_document))

        return new_documents


class StopWordDetector(object):

    def __init__(self, stop_word_proportion=0.01, tokenizer=RegexTokenizer()):
        self.tokenizer = tokenizer
        self.stop_word_proportion = stop_word_proportion
        self.unique_words = set()
        self.documents = []
        self.stopwords = []

    def fit(self, documents):
        for document in documents:
            tokenized_document = self.tokenizer.tokenize(document.lower())

            self.unique_words.update(tokenized_document)
            self.documents.append(tokenized_document)

    def fit_from_file(self, filename):
        with open(filename) as document_file:
            self.fit([document_file.read()])

    def transform(self):
        tfidf_dict = defaultdict(list)

        if len(self.documents) < 4:  # TFIDF don't work well with a small amount of documents.
            print("The number of fitted document is too low to get meaningful stopwords."
                  " Please fit some other unrelated documents.")

        # Compute TFIDF for each word in each document
        for word in self.unique_words:
            for document in self.documents:
                tf = document.count(word) / len(document)
                idf = len(self.documents) / sum([1 for doc in self.documents if word in doc])
                tfidf = tf*log(idf)

                tfidf_dict[word].append(tfidf)

        for key, value in tfidf_dict.items():
            tfidf_dict[key] = mean(value)

        # Select the (number of words)*(stop_word_proportion) with the lowest TFIDF
        stopword_number = int(len(self.unique_words)*self.stop_word_proportion)

        for _ in range(stopword_number):
            min_key = min(tfidf_dict, key=tfidf_dict.get)
            del tfidf_dict[min_key]
            self.stopwords.append(min_key)

        return self.stopwords

    def clean_tokens(self, tokens):
        for token in tokens:
            if token.lower() in self.stopwords:
                while token in tokens: tokens.remove(token)

        return tokens