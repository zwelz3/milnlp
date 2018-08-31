import re


def process_raw_into_lines(text):
    """Uses the RawTextProcessing class to process text"""
    for attr in RawTextProcessing.order:
        # Uses the order of RawTextProcessing to apply functions to process into document text
        processing_func = getattr(RawTextProcessing, attr)
        text = processing_func(text)
    return text


class RawTextProcessing(object):
    """Simple collection of attributes that should be used to pre-process raw text into a document string.
    TODO replace with waaaay more efficient process"""

    order = ['process_lines',
             'split_likely_sentences',
             'merge_likely_sentences',
             'remove_weblinks',
             'remove_short_lines',
             'remove_unlikely_sentences',
             'remove_nonascii']

    @staticmethod
    def process_lines(text):
        """create lines from text"""
        line_indicator = re.compile(r"[\n\r]")
        matches = line_indicator.finditer(text)
        init_pos = 0 if text[0] not in {"\n", "\r"} else 1
        lines = []
        for match in matches:
            end_pos = match.span()[0]
            if end_pos != 0:
                if init_pos != end_pos:
                    # print(init_pos, end_pos)
                    lines.append(text[init_pos:end_pos])
                init_pos = end_pos + 1
        return lines

    @staticmethod
    def split_likely_sentences(text):
        """Split up lines that appear to be separate sentences"""
        individualized_lines = []
        for line in text:
            split_line = [part for part in line.split('. ') if part]
            if len(split_line) == 1:
                individualized_lines.append(line)
            else:
                # add each split sentence
                for ii, part in enumerate(split_line):
                    if ii < len(split_line) - 1:
                        individualized_lines.append(part + '.')
                    else:
                        to_append = part + '.' if line[-1] == '.' else part
                        individualized_lines.append(to_append)
        return individualized_lines

    @staticmethod
    def merge_likely_sentences(text):
        # Merge lines if they don't end in .?!:
        # todo find better way to handle cases like "U.S."
        merged_lines = []
        prev_line = None
        for line in text:
            # handle sentences with spaces or end in quotes
            if line[-1] == ' ' and len(line) > 2:
                if line[-2] in '"”':
                    line_ind = -3
                else:
                    line_ind = -2
            elif line[-1] in '"”' and len(line) > 1:
                line_ind = -2
            else:
                line_ind = -1

            # Check line for merging
            if prev_line is None:
                if line[line_ind] in '.?!:' and line[line_ind - 3:line_ind].lower() != "u.s":
                    merged_lines.append(line)
                else:
                    prev_line = line
            else:  # there is a previous line
                if line.lower().endswith("u.s."):
                    line = line + ' '
                line = ''.join([prev_line, line])
                if line[line_ind] in '.?!:' and line[line_ind - 3:line_ind].lower() != "u.s":
                    merged_lines.append(line)
                    prev_line = None
                else:
                    prev_line = line
        return merged_lines

    @staticmethod
    def remove_weblinks(text):
        """Takes a list of lines and removes any web urls from the text"""
        web_filter = r"(http[\S]+|www\.[\S]+)"
        pattern = re.compile(web_filter)

        lines = []
        for line in text:
            matches = pattern.finditer(line)
            to_replace = dict()
            for match in matches:
                before = line[match.span()[0]:match.span()[1]]
                # replace match location with '' unless match[-1]=='.' then replace with '.'
                after = '' if before[-1] != '.' else '.'
                to_replace[before] = after

            for key, value in to_replace.items():
                line = line.replace(key, value)
            lines.append(line)
        return lines

    @staticmethod
    def remove_short_lines(text, min_chars=20):
        """Takes a list of lines and removes short ones"""
        lines_to_delete = []
        for line_idx, line in enumerate(text):
            # delete short lines
            if len(line) < min_chars:
                lines_to_delete.append(line_idx)

        lines_to_delete = sorted(list(set(lines_to_delete)), reverse=True)
        for lidx in lines_to_delete:
            del text[lidx]
        return text

    @staticmethod
    def remove_unlikely_sentences(text, min_chars=10, min_words=6):
        """Removes lines with less than the number of chars or words"""
        lines_to_delete = []
        for line_idx, line in enumerate(text):
            # delete short lines
            if len(line) < min_chars:
                lines_to_delete.append(line_idx)
            # Delete lines with less than min_words
            regex = re.compile(r"(?:^|[\s,-\/])([a-zA-Z]+)")
            matches = regex.finditer(line)
            words = [match.group(1) for match in matches]
            if len(words) < min_words or len(''.join(words))<min_chars:
                lines_to_delete.append(line_idx)

        lines_to_delete = sorted(list(set(lines_to_delete)), reverse=True)
        for lidx in lines_to_delete:
            del text[lidx]
        return text

    @staticmethod
    def remove_nonascii(text):
        """Removes unicode and hex from the lines"""
        lines = []
        for line in text:
            no_unicode = line.encode('ascii', errors='ignore').decode("utf-8")
            no_hex = re.sub(r'[^\x00-\x7f]', r'', no_unicode)
            lines.append(no_hex)
        return lines
