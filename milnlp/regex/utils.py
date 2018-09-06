import re
from itertools import chain


def apply_filter(pattern, text, print_res=False):
    """Apply filter to a string and return a set of words that match.

    :param pattern:
    :param text:
    :param print_res:
    :return:
    """
    pattern = re.compile(pattern)
    matches = pattern.finditer(text)

    match_set = set()

    for mm, match in enumerate(matches):
        if print_res:
            print(match)
        if not match.groups() and mm == 0:
            print("Warning: Your pattern should include a capture group. "
                  "None were found. Skipping future warnings...")
        else:
            match_set.update(set(match.groups()))  # adds all capture groups TODO remove
    return match_set


def regex_plurals(phrase):
    """Allow plural words in RegEx pattern"""
    if ' ' not in phrase and '-' not in phrase:
        # only one word in phrase
        return phrase + '[s]?'
    else:
        # multiple words in phrase
        if ' ' in phrase:
            parts = phrase.split(' ')
            for ci, constituent in enumerate(parts):
                if '-' not in constituent:
                    parts[ci] = constituent + '[s]?'
            phrase = ' '.join(parts)
        if '-' in phrase:
            parts = phrase.split('-')
            phrase = '-'.join([contituent + '[s]?' for ci, contituent in enumerate(parts)])
        return phrase


def regex_constituents(phrase):
    """Creates union RegEx pattern for consituent words"""
    if ' ' in phrase or '-' in phrase:
        # multiple words in phrase
        constituents = list(chain.from_iterable([constituent.split('-') for constituent in phrase.split(' ')]))
        return '|'.join(constituents + [phrase])
    else:
        # one word in phrase
        # print("INFO: 'constituents' flag was selected, but the supplied phrase only has one word.")  # todo logging
        return phrase


def regex_delims(phrase):
    """Adds RegEx pattern to allow special delimeters (-, ) between words separated by (- )"""
    if ' ' in phrase or '-' in phrase:
        # multiple words in phrase
        portions = list(chain.from_iterable([constituent.split('-') for constituent in phrase.split(' ')]))
        return '[\s,-]'.join(portions)  # todo check we may want ([\s-]|, ) to capture 'comma-space'
    else:
        # one word in phrase
        # print("INFO: 'special-delims' flag was selected, but the supplied phrase only has one word.")  # todo logging
        return phrase


def regex_whole_word(phrase):
    """Adds RegEx pattern to require matches to be the entire word.
       ex. 'OSSA' will not match with whole word 'on' if the Phrase is 'GLOSSARY'
    """
    if '|' in phrase:
        return '|'.join([f"(^|(?<=[\W\f])){part}[\W]" for part in phrase.split('|')])
    else:
        return f"(^|(?<=[\W\f])){phrase}[\W]"  # todo find a better way to do lookahead
