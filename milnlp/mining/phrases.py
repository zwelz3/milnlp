import re

import itertools, nltk, string
from itertools import takewhile, tee
import networkx

VALID_PATTERN = re.compile(r"[a-zA-Z]\.")
UNICODE_PATTERN = re.compile(r"[^\x00-\x7F]")


def is_valid(word):
    """Verifies the candidate is not a single letter and period (ex: 'm. ') """
    match = VALID_PATTERN.match(word)
    if match:
        return match.span() != (0, len(word.strip()))
    else:
        return True


def is_unicode(word):
    """Checks to see if a word is entirely comprised of a single unicode char.
    TODO improve to verify that % of word is not unicode?"""
    match = UNICODE_PATTERN.match(word)
    if match:
        return match.span() == (0, len(word.strip()))
    else:
        return False


def extract_candidate_words(text, good_tags={'JJ','JJR','JJS','NN','NNP','NNS','NNPS'}):
    # exclude candidates that are stop words or entirely punctuation
    punct = set(string.punctuation)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    # tokenize and POS-tag words
    tagged_words = itertools.chain.from_iterable(nltk.pos_tag_sents(nltk.word_tokenize(sent)
                                                                    for sent in nltk.sent_tokenize(text)))
    # filter on certain POS tags and lowercase all words
    candidates = [word.lower() for word, tag in tagged_words
                  if tag in good_tags and word.lower() not in stop_words
                  and not all(char in punct for char in word)
                  and is_valid(word) and not is_unicode(word)
                  and len(word) > 1]

    return candidates


def score_keyphrases_by_textrank(text, n_keywords=0.05):
    """
    TODO remove fig table etc from keywords??
    """
    # tokenize for all words, and extract *candidate* words
    words = [word.lower()
             for sent in nltk.sent_tokenize(text)
             for word in nltk.word_tokenize(sent)]
    candidates = extract_candidate_words(text)
    # build graph, each node is a unique candidate
    graph = networkx.Graph()
    graph.add_nodes_from(set(candidates))

    # iterate over word-pairs, add unweighted edges into graph
    def pairwise(iterable):
        """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)

    for w1, w2 in pairwise(candidates):
        if w2:
            graph.add_edge(*sorted([w1, w2]))

    # score nodes using default pagerank algorithm, sort by score, keep top n_keywords
    ranks = networkx.pagerank(graph)
    if 0 < n_keywords < 1:
        n_keywords = int(round(len(candidates) * n_keywords))
    word_ranks = {word_rank[0]: word_rank[1]
                  for word_rank in sorted(ranks.items(), key=lambda x: x[1], reverse=True)[:n_keywords]}
    keywords = set(word_ranks.keys())

    # merge keywords into keyphrases
    # TODO keyphrases only creates phrases from top scoring keywords, therefore if part of a phrase
    # TODO    scored poorly, then the phrase will be impossible to occur. This is a side-effect of only
    # TODO    creating 1-word candidates for selection
    keyphrases = {}
    j = 0
    for i, word in enumerate(words):
        if i < j:
            continue
        if word in keywords:
            kp_words = list(takewhile(lambda x: x in keywords, words[i:i + 10]))
            avg_pagerank = sum(word_ranks[w] for w in kp_words) / float(len(kp_words))
            # TODO note this is not actually the score of the phrase, but the average score of the constituents
            keyphrases[' '.join(kp_words)] = avg_pagerank
            # counter as hackish way to ensure merged keyphrases are non-overlapping
            j = i + len(kp_words)

    return sorted(keyphrases.items(), key=lambda x: x[1], reverse=True)
