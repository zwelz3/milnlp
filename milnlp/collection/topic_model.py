import re
#
from milnlp.regex.utils import regex_plurals, regex_constituents, regex_delims, regex_whole_word


class AbstractQuery(object):
    def __init__(self):
        self.UUID = None  # ID
        self.type = None  # simple/complex
        self.processed = False  # bool if already processed
        self.match = None  # query matches


class SimpleQuery(AbstractQuery):
    UUID_INDEX = 1

    def __init__(self, phrase):
        super().__init__()
        #
        self.type = 'simple'
        self.regex = None
        self.flags = {
            'case-sensitive': False,
            'whole-word': False,
            'special-delims': False,
            'plurals': False,
            'constituents': False,
        }
        #
        self.phrase = phrase
        self.__set_uuid()

    def __set_uuid(self):
        """Creates a uuid using the class attribute"""
        inst_uuid = "SQ_" + str(SimpleQuery.UUID_INDEX).zfill(3)
        SimpleQuery.UUID_INDEX += 1
        self.UUID = inst_uuid

    def build_regex(self):
        """Uses the instance phrase and flags to build a RegEx string"""
        regex_phrase = self.phrase
        for flag, setting in self.flags.items():
            # Use if sequence to enforce order regex_phrase is constructed
            if flag == "plurals" and setting:
                regex_phrase = regex_plurals(regex_phrase)
            if flag == "constituents" and setting:
                regex_phrase = regex_constituents(regex_phrase)
            if flag == "special-delims" and setting:
                regex_phrase = regex_delims(regex_phrase)
            if flag == "whole-word" and setting:
                regex_phrase = regex_whole_word(regex_phrase)
            # NOTE: case-sensitive flag is applied directly to compiled pattern
        self.regex = regex_phrase

    def update_flags(self, flag_dict):
        """Updates the instance flag dictionary"""
        assert self.flags.keys() == flag_dict.keys(), "Dictionary must contain same keys as instance."
        self.processed = False  # if previously processed, set to False since instance has been changed
        self.match = None  # if previously processed, set to None since instance has been changed
        for key, new_value in flag_dict.items():
            self.flags[key] = new_value
        # call RegEx builder method
        self.build_regex()

    def update_phrase(self, phrase):
        """Updates the query phrase, but retains the existing UUID (useful for tweaking low level queries)"""
        self.processed = False  # if previously processed, set to False since instance has been changed
        self.match = None       # if previously processed, set to None since instance has been changed
        self.phrase = phrase
        self.build_regex()

    def apply_query(self, file_set):
        """Run the simple query and collect results into dictionary"""
        assert type(file_set) is set, "ERROR: file_set must be of type <class 'set'>"

        for file in file_set:
            if file.endswith('.txt'):
                print("\nAnalyzing file: ", file)

                # Open and read as text
                with open(file, 'rb') as doc:
                    text = doc.read()
                text = text.decode("utf-8")

                # Step 1, get bounds of each page
                page_list = []
                starting_pos = 0
                pattern = re.compile(r"\f")  # page indicator from pdf2txt
                matches = pattern.finditer(text)  # each match is a page
                for ii, match in enumerate(matches):  # ii is page number (0 index)
                    page_break = match.span()[0]
                    page_list.append((starting_pos, page_break))
                    starting_pos = page_break + 1  # dont want to include the page break so add 1

                # Step 2, get every occurance of the RegEx pattern in the text
                match_set = set()
                if not self.flags["case-sensitive"]:
                    pattern = re.compile(self.regex, re.IGNORECASE)  # RegEx pattern
                else:
                    pattern = re.compile(self.regex)  # RegEx pattern
                matches = pattern.finditer(text)
                for match in matches:
                    occurance = match.span()[0]
                    match_set.add(occurance)

                # Step 3, resolve the match_list with the page_list to get the occurance in the current document
                pages = set()
                for page_num, page_limits in enumerate(page_list):
                    for match_loc in set(match_set):
                        if page_limits[0] <= match_loc <= page_limits[1]:
                            pages.add(page_num)
                            match_set.remove(match_loc)
                if pages:
                    print("-> Matches found on pages: ", pages)

                # Checkpoint, make sure each match was assigned a page
                assert not match_set, "WARNING: Not all matched were assigned a page."

                # Step 4, add to dictionary of matches
                if not self.match and pages:
                    self.match = {file: sorted(list(pages))}
                elif pages:
                    self.match[file] = sorted(list(pages))
        self.processed = True
