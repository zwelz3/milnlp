import os
from ..mining.phrases import score_keyphrases_by_textrank


class Document(object):
    """Simple document class to store information"""
    def __init__(self, full_path):
        self.path = full_path
        self.name = os.path.basename(full_path)
        self.directory = os.path.dirname(full_path)
        #
        self.pages = []

    def add_page(self, page):
        """"""
        self.pages.append(page)


class PbPage(object):
    """Presidential Budget style Page Object"""
    def __init__(self, text, page_num=None):
        self.raw_text = text
        self.page_number = page_num
        #
        self.program = {
            'flag': None,
            'number': None,
            'name': None,
        }
        self.exhibit = {
            'flag': None,
            'label': None,
            'year': None,
            'branch': None,
        }
        self.activity = {
            'appropriation_number': None,
            'appropriation_label': None,
            'branch': None,
            'budget_number': None,
            'budget_label': None,
        }
        self.project = {
            'number': None,
            'name': None,
        }
        self.sections = {}  # label: text
        #
        self.entities = set()
        self.acronyms = set()
        self.candidates = None


class PbGroup(object):
    """Manages a collection of pages on a specific endpoint (Program, Exhibit, etc.)"""
    def __init__(self, endpoint="program.number"):
        self.endpoint = endpoint
        #
        self.ep_value = None  # group endpoint value
        #
        self.pages = set()
        self.text = ''
        self.candidates = []
        self.entities = set()
        self.acronyms = set()
        #
        self.phrases = set()

    def add_page(self, page):
        """Adds a page's attributes to the group
        Note: there is no safeguard against adding the same page mutiple times"""
        # Step 1 - Either set group ep_value using page, or verify conformity
        attr, key = self.endpoint.split('.')
        page_ep_value = getattr(page, attr)[key]  # this gets the value we are going to use at the endpoint
        if not self.ep_value:
            self.ep_value = page_ep_value
        else:
            assert self.ep_value == page_ep_value, "Error: The page being added is not of the same enpoint value as the group."

        # Step 2 - Add the material from the page
        self.pages.add(page.page_number)
        self.text = ''.join(
            [self.text, ''.join([section for section in page.sections.values()])])  # merge all text together
        self.entities.update(page.entities)
        self.acronyms.update(page.acronyms)
        self.candidates.extend(page.candidates)  # this is a non-unique list

    def create_phrases(self, n_keywords=0.05):
        """Use the group text and collected candidates to create group phrases using TextRank"""
        self.phrases = score_keyphrases_by_textrank(self.text, n_keywords=n_keywords)

    def contains(self, words_of_interest):
        """TODO"""
        return None
