from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import os
import subprocess

from ..tokenizers import Tokenizer


class PdfConverter(object):
    """A simple class for containing a converter object for PDF files."""
    def __init__(self, password="", max_pages=0, page_nos=set(), caching=True):
        self.password = password
        self.max_pages = max_pages
        self.page_nos = page_nos
        self.caching = caching

    def convert_pdf(self, filepath, to_file=False):
        codec = 'utf-8'
        laparams = LAParams()
        retstr = io.StringIO()
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        with open(filepath, 'rb') as file:
            for page in PDFPage.get_pages(file, self.page_nos, maxpages=self.max_pages,
                                          password=self.password, caching=self.caching,
                                          check_extractable=True):
                interpreter.process_page(page)

        device.close()
        output = retstr.getvalue()
        retstr.close()
        if to_file:
            # write **Note: this file will be large if the PDF was large and mostly text, else small
            name = os.path.basename(filepath).split('.')[0]+'.txt'
            fullpath = '/'.join([os.path.dirname(filepath), name])
            with io.open(fullpath, 'w', encoding="utf-8") as file:
                file.write(output)
            return filepath[:-4]+'.txt'
        else:
            return output


def create_text(filepath, tokenizer, to_file=True, **kwargs):
    """Converts a pdf file to a plaintext"""
    conobj = PdfConverter(**kwargs)
    assert filepath.endswith('.pdf'), "This function only supports conversion from PDF."
    try:
        payload = conobj.convert_pdf(filepath, to_file)  # contains filepath or raw text
        # Check to make sure PDF is machine readable
        page_words = [len(tokenizer.to_words(page)) for page in payload.split('\f')]
        if max(page_words) < 100:
            print("WARNING: Document is likely corrupt or not a machine-readable PDF file. Skipping...")
            return 2
        if to_file:
            flag = subprocess.check_call(["attrib", "+H", filepath[:-4]+'.txt'])
        return payload
    except TypeError:
        print("WARNING: File is merged PDF and is now corrupt. Skipping...")
        return 1


def create_sumy_dom(text, tokenizer):
    """Creates a sumy style document from the sentences.
    **TODO: Assumes that paragraphs are specified by lines starting with a space """
    from sumy.models.dom import Sentence, Paragraph, ObjectDocumentModel

    paragraphs = []
    paragraph = []
    for ii, line in enumerate(text):
        if line[0] != ' ' and ii > 0:  # Last line was the last one in paragraph
            paragraphs.append(Paragraph(paragraph))  # Dump paragraph
            paragraph = []  # start new paragraph going forward
        # Process current line
        paragraph.append(Sentence(line, tokenizer))

    return ObjectDocumentModel(tuple(paragraphs))
