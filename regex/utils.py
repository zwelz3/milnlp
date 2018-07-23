import re


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
