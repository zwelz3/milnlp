import os
import re
import json
import subprocess
#
from itertools import chain
#
from .topic_model import Query
from .metadoc import create_all_metadocs, build_supermetadocs
#
from ..converters.text_utils import process_lines, remove_short_lines, merge_likely_sentences
from ..converters.text_utils import split_likely_sentences, remove_unlikely_sentences, remove_nonascii
from ..mining.phrases import score_keyphrases_by_textrank
from ..converters.pdf_to_text import create_text, create_sumy_dom
#
from sumy.models.dom import Paragraph, ObjectDocumentModel


def get_items(path, flist, dlist, lvl=0):
    """Scans a path and returns the items that were discovered at the path.
       Recursively searches so be careful calling on massive directories."""
    for item in os.listdir(path):
        pitem = os.path.join(path, item)
        if os.path.isdir(pitem):
            dlist[pitem] = lvl + 1
            print(f"\nDiscovered directory '{item}'")
            flist, dlist = get_items(pitem, flist, dlist, lvl + 1)
        elif pitem.split('.')[-1] in Collection.supported_exts:
            flist.add(pitem)
            print(f"-> Discovered file '{item}'")
    return flist, dlist


def remove_stopwords(counter, stopwords):
    """Removes stopwords from counter object
    TODO move to sumy pdf parser"""
    stopwords_toRemove = frozenset.intersection(stopwords, frozenset(counter))
    for word in stopwords_toRemove:
        _ = counter.pop(word)
    return counter


def get_metawords(threshold, document):
    """Uses the term frequency document model to return a limited number of words and their count."""
    metawords = {}
    for word, count in document._terms.most_common():
        nfreq = document.normalized_term_frequency(word)
        if nfreq > threshold and count > 1:
            # print(word, nfreq)
            metawords[word] = count
        else:
            return metawords
    return metawords


def parse_collection(flist, summarizer, token, keep_file=True):
    for f_ind, filepath in enumerate(flist):
        f_extension = filepath.split('.')[-1]
        # redundant check for now TODO remove
        supported_exts = {'pdf', 'html', 'txt'}  # TODO replace with class attribute
        if f_extension in supported_exts:
            # These need to be parsed
            print(f'Parsing {f_ind+1}/{len(flist)}: ', filepath)
            if f_extension == 'pdf':
                # print(' -- PDFs are converted to text prior to parsing in order to retain formatting.')
                # Create text data
                document_text = create_text(filepath, token, to_file=False)
                if document_text == 1:  # corrupt file error code
                    continue  # skip to next file
                if document_text == 2:  # empty/optical file error code
                    continue  # skip to next file
                # Write to file to save time later
                if keep_file:
                    with open(filepath[:-4] + '.txt', 'wb') as txt_file:
                        # raw_text = remove_nonascii([document_text])
                        txt_file.write(document_text.encode('utf-8'))
                    flag = subprocess.check_call(["attrib", "+H", filepath[:-4] + '.txt'])
                # Pre-process
                lines = process_lines(document_text)
                lines = remove_short_lines(lines)
                lines = merge_likely_sentences(lines)
                lines = split_likely_sentences(lines)
                lines = remove_unlikely_sentences(lines)
                lines = remove_nonascii(lines)
                # Parse data into document
                document = create_sumy_dom(lines, token)
                # Create naive summary for metadata document
                metasummary = '\n'.join(
                    [str(sentence) for sentence in summarizer(document, 10)])  # should return n sentences if n < 10
                # print("\nNaive document summary: \n", metasummary)
                # Phrase extraction using naive unicode candidates and TextRank
                doc_text = ' '.join([sentence._text for sentence in document.sentences])
                metawords = dict(score_keyphrases_by_textrank(doc_text,
                                                              n_keywords=0.95))  # if n < 1 it returns the percentage of results

                # these restults are now (candidate, PageRank score) format not (word, counts)
                # print("\nWords for metadata document: \n", metawords)
                # Write results to metadata document
                mdoc_name = '.'.join(filepath.split('\\')[-1].split('.')[:-1])+'.mdoc'
                mdoc_path = '\\'.join([os.path.dirname(filepath), mdoc_name])
                print("    - Updating metadata file: ", mdoc_path)
                with open(mdoc_path, 'r') as mdoc:
                    payload = json.load(mdoc)

                # add to payload
                payload["summary"] = [metasummary]
                payload["keywords"] = metawords

                # write payload
                os.remove(mdoc_path)
                flag = 1
                with open(mdoc_path, 'w') as mdoc:
                    json.dump(payload, mdoc, indent=2)
                    # reset hidden attribute
                    flag = subprocess.check_call(["attrib", "+H", mdoc_path])

                if flag != 0:
                    # remove metadata file
                    os.remove(mdoc_path)
                    assert flag == 0, "File was unable to be updated"
                else:
                    print(f"Metadata file updated.")


def reparser(docs, token, method='full'):
    """

    :param docs: either a list(doc_path) for method=='full' or
                 a dict(key=doc_path, value=set(page#)) for method=='reduced'
    :param token: tokenizer object
    :param method: 'full' uses all pages from a constituent document, 'reduced' uses only pages where query appeared
    :return:
    """
    class DummyParser(object):
        """"""
        def __init__(self, document):
            self.document = document

    parsed_docs = {}
    if method == 'full':
        assert type(docs) is list, f"Docs of type '{type(docs)}' not valid for '{method}' method."
        for f_ind, docpath in enumerate(docs):
            assert docpath[-3:] == 'txt', "Document type not supported."
            print(f" - Reading in file {f_ind+1}/{len(docs)}")
            with open(docpath, 'rb') as txt_file:
                document_text = txt_file.read().decode('utf-8')
            # Pre-process
            lines = process_lines(document_text)
            lines = remove_short_lines(lines)
            lines = merge_likely_sentences(lines)
            lines = split_likely_sentences(lines)
            lines = remove_unlikely_sentences(lines)
            lines = remove_nonascii(lines)
            # Parse data into document
            document = create_sumy_dom(lines, token)
            parsed_docs[docpath] = DummyParser(document)
    elif method == 'reduced':
        assert type(docs) is dict, f"Docs of type '{type(docs)}' not valid for '{method}' method."
        f_ind = 0
        for docpath, pages in docs.items():
            print(f" - Reading in file {f_ind+1}/{len(docs)}")
            if not pages:
                print(f"  -> No matching pages. Skipping...")
                f_ind += 1
                continue
            print(f"  -> Matching pages: {pages}")
            with open(docpath, 'rb') as txt_file:
                raw_document_text = txt_file.read().decode('utf-8')
            # Get pages from pdf2txt
            pattern = re.compile(r"\f")  # page indicator from pdf2txt
            matches = pattern.finditer(raw_document_text)  # each match is a page
            page_text = []
            starting_pos = 0
            for ii, match in enumerate(matches):  # ii is page number (0 index):
                page_break = match.span()[0]
                if ii + 1 in pages:
                    page_text.append(raw_document_text[starting_pos:page_break])
                starting_pos = page_break + 1  # don't want to include the page break so add 1
            document_text = '\f'.join(page_text)
            f_ind += 1
            # Pre-process
            lines = process_lines(document_text)
            lines = remove_short_lines(lines)
            lines = merge_likely_sentences(lines)
            lines = split_likely_sentences(lines)
            lines = remove_unlikely_sentences(lines)
            lines = remove_nonascii(lines)
            # Parse data into document
            document = create_sumy_dom(lines, token)
            parsed_docs[docpath] = DummyParser(document)
    else:
        raise TypeError("The method specified is not valid.")

    return parsed_docs


def create_superdoc(parsed_docs):
    """"""
    super_document_paragraphs = []
    for d_parser in parsed_docs.values():
        super_document_paragraphs.extend(list(d_parser.document.paragraphs))

    super_document = ObjectDocumentModel(super_document_paragraphs)
    return super_document


class Collection(object):
    """"""
    supported_exts = {'pdf', 'html', 'txt'}

    def __init__(self, collection_path):
        self.path = os.path.abspath(collection_path)
        assert os.path.isdir(self.path)
        # Initialize instance vars
        self.flist = set()
        self.flist_unprocessed = set()
        self.dlist = {self.path: 0}

    def process_collection(self):
        """Populate collection file and directory lists."""
        print(f"Processing collection at path ...\\{os.path.basename(self.path)}: \n")
        self.flist, self.dlist = get_items(self.path, self.flist, self.dlist)
        self.flist_unprocessed = set(self.flist)
        # Remove text files that are parsed pdf
        for file in set(self.flist_unprocessed):  # use set clone
            # if text file is a parsed version of pdf
            if file.endswith('.txt') and file[:-4] + '.pdf' in self.flist_unprocessed:
                self.flist_unprocessed.remove(file)  # remove so it is not processed as a normal file

            # todo handle essentially empty files here

        print(f"\nTotal number of directories:  {len(self.dlist)}")
        print(f"Total number of files:  {len(self.flist_unprocessed)} \n")

    def skip_up_to_date(self):
        """Compares any existing MDOC files modification date to the TXT parent used to populate.
        Removes from flist if already parsed and up-to-date."""
        for file in set(self.flist_unprocessed):
            # Check if mdoc exists
            mdoc_name = file[:-4] + '.mdoc'
            parsed_name = file[:-4] + '.txt'  # todo this will be different for other filetypes
            if os.path.exists(mdoc_name) and os.path.exists(parsed_name):
                # print("Pdf: \t", opath.getmtime(file), "\nMDOC: ", opath.getmtime(mdoc_name))
                if os.path.getmtime(parsed_name) < os.path.getmtime(mdoc_name):
                    print(f"MDOC is up to date. Removing from processing list...\n{file}")
                    self.flist_unprocessed.remove(file)

    def generate_metadata(self, summarizer, token, term_frequency_threshold):
        """Creates all metadata files and populates them with information.
        Rolls up directory based metadata into supermeta data files."""
        self.skip_up_to_date()
        create_all_metadocs(self.flist_unprocessed)
        parse_collection(self.flist_unprocessed, summarizer, token, term_frequency_threshold)
        build_supermetadocs(self.dlist)

    def build_query(self):
        """Uses the raw file list to instantiate a Query object"""
        return Query(self.flist)

    def make_query(self, query):
        """Runs the query on the collection"""
        # Build query object
        qobj = self.build_query()
        # Make query
        assert type(query) is list, "Query input must be a list"
        if type(query[0]) is tuple:
            qmethod = 'union'
            phrase = f"Performing {qmethod} query..."
            print(phrase)
            query_results = qobj.union_query(query)
        elif type(query[0]) is list and type(query[0][0]) is tuple:
            qmethod = 'intersect'
            phrase = f"Performing {qmethod} query..."
            print(phrase)
            query_results = qobj.intersect_query(query)
        else:
            raise TypeError('Format of query is not list of tuples (union) or list of lists of tuples (intersection')
        print("Done!")
        return query_results, qmethod

    def create_composite_document(self, query, token, method='reduced'):
        """methods = reduced and full"""
        query_results, qmethod = self.make_query(query)
        assert query_results, "The collection does not contain results for the specified query. "
        if method == 'full':
            print("Creating a composite document using the full constituent documents...")
            if qmethod == 'union':
                docs = list(
                    chain.from_iterable([list(query_results[key].keys()) for key in query_results.keys()]))
            elif qmethod == 'intersect':
                docs = list(query_results.keys())
            parsed_docs = reparser(docs, token, method=method)
            composite_doc_paragraphs = []
            for d_parser in parsed_docs.values():
                composite_doc_paragraphs.extend(d_parser.document.paragraphs)
            print("Done!")
            return ObjectDocumentModel(composite_doc_paragraphs)

        elif method == 'reduced':
            print("Creating a composite document using only the relevant pages from constituent documents...")
            if qmethod == 'union':
                merged_union_dict = dict()
                for union_phrase in query_results.keys():
                    for doc, pages in query_results[union_phrase].items():
                        if doc not in merged_union_dict:
                            merged_union_dict[doc] = pages
                        elif pages:
                            merged_union_dict[doc].update(pages)
                query_results = merged_union_dict
            parsed_docs = reparser(query_results, token, method=method)
            composite_doc_paragraphs = []
            for d_parser in parsed_docs.values():
                composite_doc_paragraphs.extend(d_parser.document.paragraphs)
            print("Done!")
            return ObjectDocumentModel(composite_doc_paragraphs)

    @staticmethod
    def summarize_composite(composite_doc, summarizer, num_sentences, *args):
        return summarizer(composite_doc, num_sentences, *args)
