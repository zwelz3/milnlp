import re


class Match(object):
    """Prototype for text that matches RegEx patterns."""

    def __init__(self, pos, ttype, groups):
        self.position = pos
        self.type = ttype
        self.capture_groups = groups


class MatchBook(object):
    """Prototype for collection of matches from the text."""

    def __init__(self, raw_text, re_filters):
        self.raw_text = raw_text
        self.filters = re_filters
        self.position_map = dict()
        #
        self.text = None

    def add_match(self, match):
        """add a match to the book"""
        self.position_map[match.position] = match

    def apply_filters(self, print_matches=False):
        """docstring"""
        # Change to script processing all filters
        for attr in dir(self.filters):
            # check por public
            if attr[0] != '_' and attr[0] == attr[0].upper():
                regex = getattr(self.filters, attr)
                pattern = re.compile(regex)
                print(f"{attr}: ", regex) if print_matches else None
                matches = pattern.finditer(self.raw_text)
                for match in matches:
                    starting_pos = match.span()[0]
                    print('pos: ', starting_pos, ' -> ', match.groups()) if print_matches else None
                    self.add_match(Match(starting_pos, attr, match.groups()))
                print("") if print_matches else None

        # Update position map
        self.sort_position_map()
        # Build text dictionary for sections
        self.text = self.build_text()

    def sort_position_map(self):
        """docstring"""
        from collections import OrderedDict
        ordered_position_map = OrderedDict()
        _ = [ordered_position_map.update({key: value}) for key, value in sorted(self.position_map.items())]
        assert len(ordered_position_map.keys()) == len(
            self.position_map.keys()), "Something went wrong will sorting the RegEx matches."
        self.position_map = ordered_position_map

    def build_text(self):
        """docstring"""
        # TODO shift top level from exhibit to program element
        exhibit_a = None  # engineering humor
        flag_print = True
        exhibit_text = []
        for position, match in self.position_map.items():
            # Check the exhibit flag group and create breaks when changes (i.e. the text block types reset)
            if match.type == 'EXHIBIT_FILTER' and match.capture_groups[0] != exhibit_a:
                print("")  # break in visuals
                exhibit_text.append(dict())  # dict for each exhibit
                flag_print = True
                exhibit_a = match.capture_groups[0]

            if flag_print:
                print(' '.join(match.capture_groups[0:2]))
                flag_print = False
            print(position, '\t', '-' * self.filters.get_weight(match.type), match.type)

            if self.filters.get_weight(match.type) > 2:
                # we are going to add the major text sections
                section = getattr(self.filters, match.type)[8:].split(')')[0]
                if section not in exhibit_text[-1].keys():
                    exhibit_text[-1][section] = match.capture_groups[0]
                else:
                    exhibit_text[-1][section] = '\n'.join([exhibit_text[-1][section], match.capture_groups[0]])

        # Trim any sections with no text contributed
        exhibit_text = [dictionary for dictionary in exhibit_text if dictionary]
        return exhibit_text
