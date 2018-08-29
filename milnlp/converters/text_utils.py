import re


class RawTextProcessing(object):
    """Simple collection of attributes that should be used to pre-process raw text into a document string."""
    order = ['process_lines',
             'remove_short_lines',
             'merge_likely_sentences',
             'split_likely_sentences',
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
                init_pos = end_pos+1
        return lines

    @staticmethod
    def remove_short_lines(text, min_chars=5):
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
    def merge_likely_sentences(text):
        from nltk.corpus import stopwords
        continuation_words = set(stopwords.words('english'))

        # Merge lines if they dont end in .?!: AND if the next line first char is a number or uncapitalized.
        merged_lines = []
        prev_line = None
        for line in text:
            if prev_line is None:
                if line[-1] in ".?!:":
                    merged_lines.append(line)
                else:
                    prev_line = line
            else:  # there is a previous line
                if prev_line[-1] not in ".?!:" and line[0].upper()==line[0] and prev_line.split(' ')[-1] in continuation_words:
                    line = ' '.join([prev_line, line])
                    if line[-1] in ".?!:":
                        merged_lines.append(line)
                        prev_line = None
                    else:
                        prev_line = line
                elif prev_line[-1] not in ".?!:" and line[0].upper()==line[0]:
                    # New sentence started on line
                    merged_lines.append(prev_line)
                    prev_line = None
                    if line[-1] in ".?!:":
                        merged_lines.append(line)
                    else:
                        prev_line = line
                else:
                    line = ' '.join([prev_line, line])
                    if line[-1] in ".?!:":
                        merged_lines.append(line)
                        prev_line = None
                    else:
                        prev_line = line
        return merged_lines

    @staticmethod
    def split_likely_sentences(text):
        """Split up lines that appear to be separate sentences"""
        individualized_lines = []
        for line in text:
            split_line = [part for part in line.split('. ') if part]
            if len(split_line)==1:
                individualized_lines.append(line)
            else:
                # add each split sentence
                for ii, part in enumerate(split_line):
                    if ii<len(split_line)-1:
                        individualized_lines.append(part+'.')
                    else:
                        to_append = part+'.' if line[-1]=='.' else part
                        individualized_lines.append(to_append)
        return individualized_lines

    @staticmethod
    def remove_unlikely_sentences(text, min_chars=10, min_words=4):
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
