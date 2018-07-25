import re
import nltk
import zipfile   # only for exception handling

from ._compat import to_string, to_unicode
from .utils import normalize_language


class NltkWordTokenizer(object):
    def tokenize(self, text):
        return nltk.word_tokenize(text)


class Tokenizer(object):
    """Language dependent tokenizer of text document."""

    WORD_PATTERN = re.compile(r"[a-zA-Z]+-[\w]+|[a-zA-Z]+[\d]{1,6}|[a-zA-Z'_]+")
    # Note "word, word" returns true

    def __init__(self, language):
        language = normalize_language(language)
        self._language = language

        self._sentence_tokenizer = self._get_sentence_tokenizer(language)
        self._word_tokenizer = self._get_word_tokenizer(language)

    @property
    def language(self):
        return self._language

    @staticmethod
    def _get_sentence_tokenizer(language):
        try:
            path = to_string("tokenizers/punkt/%s.pickle") % to_string(language)
            return nltk.data.load(path)
        except (LookupError, zipfile.BadZipfile):
            raise LookupError(
                "NLTK tokenizers are missing. Download them by following command: "
                '''python -c "import nltk; nltk.download('punkt')"'''
            )

    @staticmethod
    def _get_word_tokenizer(language):
        """
        TODO implement custom language tokenizers (i.e. gov/mil/academic)
        :param language:
        :return:
        """
        if language:
            print(f"Using default NLTK tokenizer not {language}. Custom language tokenizers not available.")
        return NltkWordTokenizer()

    def to_sentences(self, paragraph):
        sentences = self._sentence_tokenizer.tokenize(to_unicode(paragraph))
        return tuple(map(str.strip, sentences))

    def to_words(self, sentence):
        words = self._word_tokenizer.tokenize(to_unicode(sentence))
        return tuple(filter(self.is_word, words))

    def is_word(self, word):
        """Filters out non-words as defined by the word patters (regex)"""
        # REPLACE _WORD_PATTER HERE TODO
        return bool(self.WORD_PATTERN.search(word))
