from milnlp.collection.utils.filesystem import check_ext
from milnlp.parsers.pdf import pdf_parser
from milnlp.mining.phrases import score_keyphrases_by_textrank
from milnlp.converters.text_utils import RawTextProcessing
from milnlp.converters.pdf_to_text import create_sumy_dom
#
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


class SingleDocSummarizer(object):
    """Creates a summary and keywords for a single document"""
    def __init__(self, tokenizer, summarizer):
        LANGUAGE = "english"
        stemmer = Stemmer(LANGUAGE)
        self.summarizer = summarizer(stemmer)
        self.summarizer.stop_words = get_stop_words(LANGUAGE)
        self.token = tokenizer(LANGUAGE)
        #
        self.summary = None
        self.words = None

    def process_document(self, file_path):
        """Creates a summary and key words for the single document"""
        # Parse or load file
        needs_parsing = not check_ext(file_path)
        print("Does file need to be parsed? ", needs_parsing)
        if needs_parsing:
            print("Parsing file...")
            status, document_text = pdf_parser(file_path, self.token, keep_file=False)
            assert status == 0, "Something went wrong."
            print("Done!")
        else:
            print("Loading file...")
            assert file_path[-4:] == '.pdf'
            with open(file_path[:-4] + '.txt', 'rb') as txt_file:
                document_text = txt_file.read().decode('utf-8')

        # Pre-process
        for attr in RawTextProcessing.order:
            # Uses the order of RawTextProcessing to apply functions to process into document text
            processing_func = getattr(RawTextProcessing, attr)
            document_text = processing_func(document_text)

        # Parse data into sumy document object
        document = create_sumy_dom(document_text, self.token)

        # Create summary for document
        self.summary = self.summarizer(document, 5)

        # Phrase extraction using naive unicode candidates and TextRank
        doc_text = ' '.join([sentence._text for sentence in document.sentences])  # text only protected/private access
        self.words = dict(score_keyphrases_by_textrank(doc_text, n_keywords=0.15))  # results are (candidate, score)
