platform_test_phrase = """
F 35, F35, F-35, f-35, f35
ALQ 121, ALQ121, ALQ-121
F 15c/C, F15c/C, F-15c/C

Alq 121, alq 121
1234567
123ABCD
"""

acronym_test_phrase = """
Analysis of Alternatives (AoA)
AOA, TTF
AoA
aoA
aoa
AOa
aOa

AFSIM TRIAM
AFSIM, TRIAM
"""


class UnclassifiedFilters(object):
    def __init__(self):
        # Platforms/Systems
        self.NUMERIC_ID_FILTER = r"([A-Z]+-[\d]+|[A-Z]+ [\d]+|[A-Z]+[\d]+)"                  # F15, F 15, F-15
        self.ALPHANUMERIC_ID_FILTER_1 = r"([A-Z]+ [\d]+[a-zA-Z]+|[A-Za-z]+-[\d]+[a-zA-Z]+)"  # F-15C
        self.ALPHANUMERIC_ID_FILTER_2 = r"([a-zA-Z]+[\d]+[a-zA-Z]*)"                         # F15C
        # Acronyms
        self.UPPERCASE_FILTER = r"(?:[^a-zA-Z])([A-Z]{2,6})(?:[^a-zA-Z])"    # AOA, TTF
        self.UPPERCASE_SEPARATED_FILTER = r"([A-Z]{2,6})(?: )([A-Z]{2,6})"   # AFSIM TRIAM (also 'openMDAO Model')
        self.MIXEDCASE_CENTER_FILTER = r"([A-Z][a-z]+[A-Z])"                 # AoA, AooA (also 'oAoAo')
        # TODO Acronym backend, Abbreviations
