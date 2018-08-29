import subprocess
#
from ..converters.pdf_to_text import create_text


def pdf_parser(file_path, token, keep_file=True):
    """Converts PDF files into raw text

    :param file_path:   path to file
    :param token:       tokenizer object
    :param keep_file:   bool to write parsed document text to output txt file

    :return: status, document text string
    """
    # Create text data from pdf file
    document_text = create_text(file_path, token, to_file=False)

    # Check for errors during conversion
    if document_text == 1:  # corrupt file error code
        return 1, None
    if document_text == 2:  # empty/optical file error code
        return 2, None

    # Write to file to save time later
    if keep_file:
        with open(file_path[:-4] + '.txt', 'wb') as txt_file:
            txt_file.write(document_text.encode('utf-8'))
        flag = subprocess.check_call(["attrib", "+H", file_path[:-4] + '.txt'])
        if flag != 0:
            print("WARNING: Converted text file was unable to be set to 'hidden'")

    return 0, document_text
