import re


class Query(object):
    """Query object containing functionality for searching a collection of files.

    flist: List of text files to be searched. This is often generated with the collection object.
    """
    def __init__(self, flist):
        self.files = flist

    def union_query(self, query_list, case_sensitive=False, buffer=0):
        """Takes a query list and list of .txt file paths and returns matching files and their page numbers.
           Note, the check is case insensitive.
           Note, if a query has a single item, the tuple must be created correctly ('item_one',) <- notice the comma.

           query_list: list of tuples with permutations of the same query term
                       i.e. [('F35', 'F-35', 'F 35'), ('ALR-69A', 'ALR69A', '69A')]

           file_list: list of full filepaths
        """
        # todo check to make sure every query is a tuple
        query_results = dict()
        for query in query_list:
            query_results[', '.join([element for element in query])] = dict()

        for file in self.files:
            if file.endswith('.txt'):
                # print("\nAnalyzing file: ", file)

                # Open and read as text
                with open(file, 'rb') as doc:
                    text = doc.read()
                text = text.decode("utf-8")

                # Get pages from pdf2txt
                pattern = re.compile(r"\f")  # page indicator from pdf2txt
                matches = pattern.finditer(text)  # each match is a page
                starting_pos = 0
                for ii, match in enumerate(matches):  # ii is page number (0 index)
                    # print(" -> Analyzing page: ", ii+1)
                    page_break = match.span()[0]
                    # print(f"Page break #{ii+1} at char '{page_break}'")
                    # print(f" -> range {starting_pos} to {page_break}")
                    page_text = text[starting_pos:page_break]
                    starting_pos = page_break + 1  # dont want to include the page break so add 1

                    for query in query_list:
                        result_key = ', '.join([element for element in query])  # used for dict
                        re_pattern = '|'.join([term for term in query])
                        if case_sensitive:
                            re_filter = re.compile(re_pattern)
                        else:
                            re_filter = re.compile(re_pattern, re.IGNORECASE)
                        if re_filter.findall(page_text):
                            # print("  -->  Found at least 1 match for pattern: ", re_pattern)
                            if file not in query_results[result_key]:
                                query_results[result_key][file] = set()
                            query_results[result_key][file].update({ii + 1})  # todo also add buffer pages

        return query_results

    def intersect_query(self, query_set, case_sensitive=False, buffer=0):
        """Takes a list of query_lists (for union) and finds the intersection.
           Uses the regex_query as a baseline search, therefore the following behavior should be expected:
             - tuples within a list of queries are unionized
                   **Note: this makes tuple lists and tuple contents equivalent [[('a',),('b',)]] == [[('a','b')]]
             - tuples across the query set (list of lists) are intersected
        """
        assert len(query_set) > 1, "Cannot compute intersection of a single query"''
        # todo check to make sure every query is a tuple
        for ii, queries in enumerate(query_set):
            results = self.union_query(queries, case_sensitive=case_sensitive)  # query results for one 'queries'
            files = set()
            # add files from each query to a set
            for query_request in results.keys():
                files.update(results[query_request].keys())

            # This produces the file and pages that each and every query portion of
            # an individual in the query set are found at
            query_fp_dict = {}
            for file in files:
                for fp_dict in results.values():  # file: page dictionary
                    if file in fp_dict:  # file the current file is in the query dictionary
                        pages = fp_dict[file]
                        if file not in query_fp_dict:
                            query_fp_dict[file] = pages
                        else:
                            query_fp_dict[file].update(pages)

            # Note that query_fp_dict is using union, therefore it must now be cast to
            # the final dictionary that will find intersection
            # todo add buffer handle
            if ii > 0:
                intersected = {}
                shared_files = set(p_query_fp_dict.keys()).intersection(set(query_fp_dict.keys()))
                for file in shared_files:
                    shared_pages = p_query_fp_dict[file].intersection(query_fp_dict[file])
                    # print(p_query_fp_dict[file],query_fp_dict[file])
                    # print(file.split('\\')[-1])
                    # print("Shared pages: ",shared_pages)
                    intersected[file] = shared_pages
            else:
                intersected = query_fp_dict
            print(f"Number of files matching all queries up to and including query #{ii+1}:  {len(intersected)}")
            p_query_fp_dict = query_fp_dict

        return intersected
