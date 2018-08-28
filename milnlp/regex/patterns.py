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
    filter_dict = {
        'PROGRAM_ELEMENT_FILTER': r"((?:PE\s|)(?:[\d]{7}[A-Z]))[^\w]",
        'FISCAL_YEAR_FILTER': r"(?:^|[^\w])(FY(?:[^\w]|-|)(?:[\d]{4}|[\d]{2}))",
        'ENTITY_STYLE1_FILTER': r"([A-Z]+-[\d]+|[A-Z]+ [\d]+|[A-Z]+[\d]+)(?:[^\w])",
        'ENTITY_STYLE2_FILTER': r"([A-Z]+ [\d]+[a-zA-Z]+|[A-Za-z]+-[\d]+[a-zA-Z]+)",
        'ENTITY_STYLE3_FILTER': r"([a-zA-Z]+[\d]+[a-zA-Z]*)",
        'UPPERCASE_FILTER': r"(?:[^a-zA-Z])([A-Z]{2,6})(?:[^a-zA-Z])",
        'MIXEDCASE_CENTER_FILTER': r"([A-Z][a-z]+[A-Z])",
    }

    def __init__(self):
        pass
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
    # _section_suffix = r")(?:(?:(?:\().*?(?:\)))|)(.*?)(?:\(\.\.\.| [A-Z]\.)"
    # _section_suffix = r")\n(?:((?:.*\n)*?)(?:[A-Z]+\.)|((?:.*\n)*?)(?:.*\.\.\.))"
    _section_suffix = r")[\n\r]+(?:((?:.*\n)*?)(?:[A-Z]+\.)|((?:.*\n)*?)(?:.*\.\.\.))"
    # PB Doc Filters w/ group description comments
    # EXHIBIT_FILTER = r"Exhibit ([A-Z]-[\d]), (.*?): (?:PB) ([\d]{4})(?:.*?)(Air Force|Army|Navy|Marines)"
    EXHIBIT_FILTER = r"Exhibit\s([A-Z]+-[\w]+),\s(.*?):\s(?:PB\s)([\d]{4})\s(Air Force|Army|Navy|Marines)"
    # Group 1 - Exhibit flag (ex: Exhibit R-2)
    # Group 2 - Identifier   (ex: RDT&E Budget Item Justification
    # Group 3 - PB Year      (ex: PB 2019)
    # Group 4 - Branch       (ex: Air Force)
    # ACTIVITY_FILTER = r"([\w\/]*?)(?: Activity )(\d+): (.*?), (Air Force|Army|Navy|Marines) \/ " \
    #                  r"(?:[A-Z]+) (\d+): ((?:\w+ +)+)"
    # ACTIVITY_FILTER = r"Appropriation\/Budget Activity[\s\n]([\d]{3,6})(?:(?:\:\s)(.*), " \
    #                  r"(Air Force|Army|Navy|Marines)|.*)\s\/\s(?:(\d)\n|([\w]{1,4})\s([\d]+):\n(.*))"
    ACTIVITY_FILTER = r"Appropriation\/Budget Activity[\s\r\n]+([\d]{3,6})(?:(?:\:\s)(.*), " \
                      r"(Air Force|Army|Navy|Marines)|.*)\s\/\s(?:(\d)[\n\r]+|([\w]{1,4})\s([\d]+):[\n\r]+(.*))"
    # Group 1 - Appropriation type   (ex: Appropriation/Budget)
    # Group 2 - Appropriation #      (ex: Activity '3600')
    # Group 3 - Appropriation label  (ex: Research, Development, Test & Evaluation)
    # Group 4 - Branch          (ex: Air Force)
    # Group 5 - Budget Identifier    (ex: BA '7')
    # Group 6 - Category        (ex: Operational Systems Development)
    # PROGRAM_FILTER = r"([A-Z]+-[\d]+) Program Element \(Number\/Name\) (?:[A-Z]+ )(\w+) " \
    #                 r"(?:\/ )((?:\w+\s+)+)"
    # PROGRAM_FILTER = r"([A-Z]+-[\d]+)\sProgram Element \(Number\/Name\)[\s\n](?:PE\s|)([\d]{7}[A-Z])\s\/\s(.*)"
    PROGRAM_FILTER = r"([A-Z]+-[\d]+)\sProgram Element \(Number\/Name\)[\s\n\r]+(?:PE\s|)([\d]{7}[A-Z])\s\/\s(.*)"
    # Group 1 - Program flag    (ex: R-1)
    # Group 2 - Element #       (ex: PE '0605018F')
    # Group 3 - Element name    (ex: AF Integrated Personnel and Pay System) TODO add acronym support
    # PROJECT_FILTER = r"Project\s\(Number\/Name\)[\n]([\d]{5,8})\s\/\s(.*)"
    PROJECT_FILTER = r"Project\s\(Number\/Name\)[\n\r]+([\d]{5,8}[A-Z]*)\s\/\s(.*)"
    # Group 1 - Project #       (ex: 674101)
    # Group 2 - Project Name    (ex: Aircraft training)
    # MDBIJ_CHUNK_FILTER = r"(?: A\. Mission Description and Budget Item Justification" + _section_suffix
    MDBIJ_CHUNK_FILTER = r"(?:[A-Z]+\.\sMission\sDescription\sand\sBudget\sItem\sJustification"+_section_suffix
    # APP_CHUNK_FILTER = r"(?: C\. Accomplishments/Planned Programs" + _section_suffix
    APP_CHUNK_FILTER = r"(?:[A-Z]+\.\sAccomplishments\/Planned\sPrograms\s\(\$ in Millions\)"+_section_suffix
    # OPFS_CHUNK_FILTER = r"(?: D\. Other Program Funding Summary" + _section_suffix
    OPFS_CHUNK_FILTER = r"(?:[A-Z]+\.\sOther\sProgram\sFunding\sSummary\s\(\$ in Millions\)"+_section_suffix
    # AS_CHUNK_FILTER = r"(?: E\. Acquisition Strategy" + _section_suffix
    AS_CHUNK_FILTER = r"(?:[A-Z]+\.\sAcquisition\sStrategy"+_section_suffix
    # Group 1 - Text chunk from section to end of page or next section
    # TODO do we want date???

    def __init__(self):
        pass
        # TODO do we care about this:
        """ This program is in Budget Activity 7, Operational System Development,
        because this budget activity includes development efforts to upgrade systems
        that have beenfielded or have received approval for full rate production and
        anticipate production funding in the current or subsequent fiscal year."""
        # TODO add greedy option for grabbing 2 return lines vs 1