import re
import nltk


# Regex Patterns
page_pattern = re.compile(r"\f")
unicode_pattern = re.compile(r"[^\x00-\x7F]")
wordref_pattern = re.compile(r"([a-z]{3,})[\[]?[\d]+[,-]?[\d]*[\]]?")  # https://regexr.com/4213c

# Sets for lookup
normal_chars = set([char for char in ":,.?!-\"\'\(\)"])
normal_punct = set([char for char in ".?!\"\'\)"])
basic_pos = {'JJ','JJR','JJS','NN','NNP','NNS'}  # these POS alone are not enough for a valid "natural language" sentence


class RawTextProcessing(object):
    """
    TODO - Priority
        headings currently getting merges into following sentence
        remove chunks that only contain bibliography citations
        merge sentences on (fig. Fig. etc. e.g. i.e. et.)

    TODO - Less Important
        remove unicode??
        remove sentence if email exists in sentence
        remove sentence if url exists and sentence has less than N words (tunable)
        remove sentence if more than N personal pronouns (PRP) are used (tunable)
        remove in-text citations**


    **In-text:
        author = "(?:[A-Z][A-Za-z'`-]+)"
        etal = "(?:et al.?)"
        additional = "(?:,? (?:(?:and |& )?" + author + "|" + etal + "))"
        year_num = "(?:19|20)[0-9][0-9]"
        page_num = "(?:, p.? [0-9]+)?"  # Always optional
        year = "(?:, *"+year_num+page_num+"| *\("+year_num+page_num+"\))"
        regex = "(" + author + additional+"*" + year + ")"
        matches = re.findall(regex, text)
    """
    # Tunable parameters
    TUNABLE_MAX_NUPW = 0.05  # the maximum number of unicode symbols per words (freq) for a sentence before the sentence is excluded
    TUNABLE_MIN_SPC = 2   # the minimum number of sentences per 1 chunk before the chunk is discarded.
    # TUNABLE_MAX_CPU = 2   # the maximum number of expected characters in any unit (cm^3 = 2) used to discard reference indices (something23)
    TUNABLE_MIN_WPS = 6   # the minimum number of nltk tokenized 'words' in a sentence before the sentence is thrown out
    TUNABLE_MAX_WPS = 50  # the maximum number of nltk tokenized 'words' in a sentence before the sentence is thrown out

    @classmethod
    def process_raw_into_lines(cls, raw_text, tokenizer):
        pages = page_pattern.finditer(raw_text)

        all_sentences = []
        processed_pages = []
        start = 0
        # Break document into pages
        for pi, page in enumerate(pages):
            end, new_start = page.span()
            page_text = raw_text[start:end]
            start = new_start

            # Break page into chunks
            processed_chunks = []
            chunks = page_text.split('\n\n')
            for ci, chunk in enumerate(chunks):
                # Remove newlines from chunk
                chunk_text = chunk.replace('\n', ' ').replace('  ',
                                                              ' ')  # todo this is merging headers into sentences. Replace with intelligent check
                                                                    # ex: normal_document
                                                                    # also appears to be merging tables

                # Break chunk into sentences
                processed_sentences = []
                for sentence in nltk.sent_tokenize(chunk_text):

                    # Add steps here to clean up words+ref (i.e. parnel28)
                    replacement_map = [(match.group(0), match.group(1)) for match in wordref_pattern.finditer(sentence)]
                    for before, after in replacement_map:
                        sentence = sentence.replace(before, after)

                    # Get words and POS-tagged words for next steps
                    words = nltk.word_tokenize(sentence)
                    num_valid_words = sum([tokenizer._is_word(word) for word in words])
                    pos_words = nltk.pos_tag(
                        words)  # todo '|' char is being tagged as word instead of symbol (i.e. JJ, NN)
                                # todo likely a unicode error (nltk not trained on unicode for english?)

                    # Test number of unicode symbols in the sentence
                    nu = len(unicode_pattern.findall(sentence))  # nu = number of unicode chars
                    nupw = nu / len(words)
                    # Test number of NN+JJ to make sure sentence is 'natural'
                    explanatory_pos = set([pos for _, pos in pos_words]).difference(normal_chars.union(basic_pos))

                    # Add to sentences if passing checks
                    if nupw <= cls.TUNABLE_MAX_NUPW and \
                            cls.TUNABLE_MAX_WPS > num_valid_words >= cls.TUNABLE_MIN_WPS and \
                            explanatory_pos:
                        # todo implement check to make sure some puntuation terminates the sentence, or
                        # todo   else it will be improperly merged into a sumy DOM.
                        if sentence.strip()[-1] not in normal_punct:
                            sentence += '.'
                        processed_sentences.append(sentence)
                        all_sentences.append(sentence)

                # Add to chunks if passing checks
                if len(processed_sentences) >= cls.TUNABLE_MIN_SPC:
                    processed_chunks.append(processed_sentences)

            processed_pages.append(processed_chunks)

        return all_sentences
