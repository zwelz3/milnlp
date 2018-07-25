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

# If using custom options
"""
import configparser

config = configparser.ConfigParser()
config.read('FILE.INI')
print(config['DEFAULT']['path'])     # -> "/path/name/"
config['DEFAULT']['path'] = '/var/shared/'    # update
config['DEFAULT']['default_message'] = 'Hey! help me!!'   # create

with open('FILE.INI', 'w') as configfile:    # save
    config.write(configfile)
"""


class UnclassWordFilters(object):
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
        #            ADD HERE


class UnclassPbFilters(object):
    # protected members
    _weights = {
        'EXHIBIT_FILTER': 1,
        'ACTIVITY_FILTER': 2,
        'PROGRAM_FILTER': 2,
        'MDBIJ_CHUNK_FILTER': 3,
        'APP_CHUNK_FILTER': 3,
        'OPFS_CHUNK_FILTER': 3,
        'AS_CHUNK_FILTER': 3,
    }
    _section_suffix = r")(?:(?:(?:\().*?(?:\)))|)(.*?)(?:\(\.\.\.| [A-Z]\.)"

    # PB Doc Filters w/ group description comments
    EXHIBIT_FILTER = r"Exhibit ([A-Z]-[\d]), (.*?): (?:PB) ([\d]{4})(?:.*?)(Air Force|Army|Navy|Marines)"
    # Group 1 - Exhibit flag (ex: Exhibit R-2)
    # Group 2 - Identifier   (ex: RDT&E Budget Item Justification
    # Group 3 - PB Year      (ex: PB 2019)
    # Group 4 - Branch       (ex: Air Force)
    ACTIVITY_FILTER = r"([\w\/]*?)(?: Activity )(\d+): (.*?), (Air Force|Army|Navy|Marines) \/ " \
                      r"(?:[A-Z]+) (\d+): ((?:\w+ +)+)"
    # Group 1 - Appropriation type   (ex: Appropriation/Budget)
    # Group 2 - Appropriation #      (ex: Activity '3600')
    # Group 3 - Appropriation label  (ex: Research, Development, Test & Evaluation)
    # Group 4 - Branch          (ex: Air Force)
    # Group 5 - Budget Identifier    (ex: BA '7')
    # Group 6 - Category        (ex: Operational Systems Development)
    PROGRAM_FILTER = r"([A-Z]+-[\d]+) Program Element \(Number\/Name\) (?:[A-Z]+ )(\w+) " \
                     r"(?:\/ )((?:\w+\s+)+)"
    # Group 1 - Program flag    (ex: R-1)
    # Group 2 - Element #       (ex: PE '0605018F')
    # Group 3 - Element name    (ex: AF Integrated Personnel and Pay System) TODO add acronym support
    MDBIJ_CHUNK_FILTER = r"(?: A\. Mission Description and Budget Item Justification" + _section_suffix  # Mission Description and Budget Item Justification
    APP_CHUNK_FILTER = r"(?: C\. Accomplishments/Planned Programs" + _section_suffix  # Accomplishments/Planned Programs
    OPFS_CHUNK_FILTER = r"(?: D\. Other Program Funding Summary" + _section_suffix  # Other Program Funding Summary
    AS_CHUNK_FILTER = r"(?: E\. Acquisition Strategy" + _section_suffix  # Acquisition Strategy
    # Group 1 - Text chunk from section to end of page or next section

    def __init__(self):
        pass
        # TODO do we care about this:
        """ This program is in Budget Activity 7, Operational System Development,
        because this budget activity includes development efforts to upgrade systems
        that have beenfielded or have received approval for full rate production and
        anticipate production funding in the current or subsequent fiscal year."""
        # TODO fix for inconsistent patterns
        #    Appropriation/Budget Activity
        #             3600 / 7
        #             3600: Research, Development, Test & Evaluation, Air Force / BA 7:Operational Systems Development
        # TODO fix for Exhibit can be 1, 2, 3, but also 1A-1Z

    def get_weight(self, label):
        """Returns the weight for a label from the protected member"""
        try:
            return self._weights[label]
        except KeyError:
            print("The requested label does not have a weight. Defaulting to 0...")
            return 0
