import sys
import shelve
import subprocess
from os import getcwd, path, remove
#
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QPushButton, QRadioButton, QLineEdit, QCheckBox, QComboBox, QPlainTextEdit, QProgressBar
from PySide2.QtWidgets import QWidget, QAction, QGroupBox, QFileDialog, QLabel, QTextEdit, QSpinBox, QTabWidget
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile, QObject, QPersistentModelIndex, QCoreApplication
#
from milnlp.gui.utils import load_query_list, process_query_list
#
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from milnlp.collection.collection import Collection
from milnlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.summarizers.lex_rank import LexRankSummarizer as LexSummarizer
from milnlp.sumyplus.SingleDocSummarizer import SingleDocSummarizer

#
from milnlp.collection.utils.qol import doc_to_text
from milnlp.mining.phrases import score_keyphrases_by_textrank


def purge_matches(query):
    """purges all matches from query object"""
    query.match = None
    query.processed = False
    if query.type == 'complex':
        for dependency in query._dependencies:
            purge_matches(dependency)


def open_query_builder():
    """Opens the query builder tool from within the summary tool"""
    loc = path.dirname(__file__)
    if not loc:
        loc = getcwd()
    if not path.exists(loc+'\\'+"query_builder.py"):
        print("The query builder tool is not installed.")
        return 1
    subprocess.Popen('python -c "from milnlp.gui import query_builder; query_builder.run()"')


def run():
    app = QApplication(sys.argv)
    loc = path.dirname(__file__)
    form = Form(loc+'\\'+"summary_tool.ui", app)
    sys.exit(app.exec_())


class Form(QObject):
    """Basic form class for loading uifile"""
    def __init__(self, ui_file, application, parent=None):
        super(Form, self).__init__(parent)
        self.application = application

        # ================================
        #    Load Window
        # ================================
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # ===================================
        # Instantiate some window properties
        # ===================================
        # Collection
        self.collection_path = None
        self.collection_working_path = getcwd()
        self.cobj = None
        self.document = None
        self.matches = None
        self.shelf_path = None
        self.shelf_working_path = getcwd()
        self.query_list = []  # visual list for the GUI
        self.queries = []  # shelve object list
        self.formatted_queries = []
        self.selected_query = None

        # Single Document
        self.file_path = None
        self.working_path = getcwd()

        # Mutual
        self.results = None
        self.num_sentences = 5
        self.num_keywords = 10

        # ================================
        # Locate and bind window children
        # ================================
        # menuBar -> menuTools
        action_load = self.window.findChild(QAction, 'actionLoadQL')
        action_load.triggered.connect(self.browse_and_load)
        action_refresh = self.window.findChild(QAction, 'actionRefresh')
        action_refresh.triggered.connect(self.refresh)

        # centralWidget -> tabWidget
        self.tab_widget = self.window.findChild(QTabWidget, 'tabWidget')

        # -----------------------------
        # tabWidget -> Collection Panel
        # -----------------------------

        # centralWidget -> collection
        self.line_collection_path = self.window.findChild(QPlainTextEdit, 'collectionPathInput')
        self.line_collection_path.textChanged.connect(self.check_collection_path)
        butt_browse_collection_path = self.window.findChild(QPushButton, 'collectionBrowseButton')
        butt_browse_collection_path.clicked.connect(self.browse_collection_path)

        # centralWidget -> Process Collection
        self.butt_process_collection_processing = self.window.findChild(QPushButton, 'processButton')
        self.butt_process_collection_processing.clicked.connect(self.process_configuration)
        self.prog_bar = self.window.findChild(QProgressBar, 'progressBar')
        self.prog_label = self.window.findChild(QLabel, 'progressLabel')

        # centralWidget -> queryFiles
        self.line_query_path = self.window.findChild(QPlainTextEdit, 'queryPathInput')
        self.line_query_path.textChanged.connect(self.check_query_path)
        butt_browse_query_path = self.window.findChild(QPushButton, 'queryBrowseButton')
        butt_browse_query_path.clicked.connect(self.browse_shelf_path)
        self.butt_load_query_path = self.window.findChild(QPushButton, 'queryLoadButton')
        self.butt_load_query_path.clicked.connect(self.load_shelf_file)
        butt_open_query_builder = self.window.findChild(QPushButton, 'openQueryBuilderButton')
        butt_open_query_builder.clicked.connect(open_query_builder)

        # centralWidget -> querySelection
        self.combo_query = self.window.findChild(QComboBox, 'queriesCombo')
        self.combo_query.currentIndexChanged.connect(self.set_query_combo)
        self.clear_query = self.window.findChild(QPushButton, 'clearQueryButton')
        self.clear_query.clicked.connect(self.clear_query_box)

        # centralWidget -> Query Options
        self.spin_sentence_buffer = self.window.findChild(QSpinBox, 'spinSentenceBuffer')

        # centralWidget -> Summary Options
        self.radio_full = self.window.findChild(QRadioButton, 'radioFull')
        self.radio_reduced = self.window.findChild(QRadioButton, 'radioReduced')
        self.radio_reduced.setChecked(True)  # reduced by default
        self.spin_num_sentences_collection = self.window.findChild(QSpinBox, 'spinSentencesCollection')
        self.spin_num_sentences_collection.valueChanged.connect(self.set_sentences_collection)
        self.spin_num_words_collection = self.window.findChild(QSpinBox, 'spinWordsCollection')
        self.spin_num_words_collection.valueChanged.connect(self.set_words_collection)

        # centralWidget -> Apply Query
        self.butt_apply_query = self.window.findChild(QPushButton, 'applyQueryButton')
        self.butt_apply_query.clicked.connect(self.apply_query)

        # -----------------------------------
        # tabWidget -> Single Document Panel
        # -----------------------------------

        # centralWidget -> file
        self.line_file_path = self.window.findChild(QPlainTextEdit, 'filePathInput')
        self.line_file_path.textChanged.connect(self.enable_summary_button)
        butt_browse_file_path = self.window.findChild(QPushButton, 'fileBrowseButton')
        butt_browse_file_path.clicked.connect(self.browse_file_path)

        # centralWidget -> Customization
        self.spin_num_sentences = self.window.findChild(QSpinBox, 'spinSentences')
        self.spin_num_sentences.valueChanged.connect(self.set_sentences)
        self.spin_num_words = self.window.findChild(QSpinBox, 'spinWords')
        self.spin_num_words.valueChanged.connect(self.set_words)

        # centralWidget -> Apply Query
        self.butt_summarize = self.window.findChild(QPushButton, 'summarizeButton')
        self.butt_summarize.clicked.connect(self.apply_summary)

        # -----------------------------
        # tabWidget -> Results Panel
        # -----------------------------

        # centralWidget -> view results
        self.results_text = self.window.findChild(QPlainTextEdit, 'outputText')
        self.results_text.textChanged.connect(self.enable_save_results_button)
        self.butt_save_results = self.window.findChild(QPushButton, 'saveOutputButton')
        self.butt_save_results.clicked.connect(self.write_results)

        # -----------------------------
        # tabWidget -> Results Panel
        # -----------------------------

        # centralWidget -> view matches
        self.matches_text = self.window.findChild(QPlainTextEdit, 'outputMatches')

        # ========
        #   Show
        # ========
        self.window.show()

    #
    #     METHODS BELOW   ---------------------------------------
    #

    def resize_widget(self, shape_tuple):
        """ """
        self.window.resize(shape_tuple[0], shape_tuple[1])

    def minimize_widget(self):
        """ """
        self.resize_widget((430, 530))

    def set_sentences_collection(self):
        """ """
        self.num_sentences = self.spin_num_sentences_collection.value()
        self.spin_num_sentences.setValue(self.num_sentences)

    def set_words_collection(self):
        """ """
        self.num_keywords = self.spin_num_words_collection.value()
        self.spin_num_words.setValue(self.num_keywords)

    def browse_collection_path(self):
        """Creates a browse session so the user can locate a collection path"""
        # Get the path to collection
        self.collection_path = QFileDialog.getExistingDirectory(None, "Locate Collection Root",
                                                                self.collection_working_path)
        # todo add handle for canceling the load
        # Update working_path to save user preference
        self.collection_working_path = self.collection_path
        # Update line edit
        self.line_collection_path.setPlainText(self.collection_path)

    def check_collection_path(self):
        """ """
        temp_path = self.line_collection_path.toPlainText()

        self.prog_bar.setValue(0)
        self.prog_label.setText("")

        if temp_path and path.exists(temp_path):
            self.butt_process_collection_processing.setEnabled(True)
            self.collection_path = self.line_collection_path.toPlainText()
            self.collection_working_path = self.collection_path
            #
            self.butt_apply_query.setEnabled(False)  # if collection path is changed, require re-process
        else:
            self.butt_process_collection_processing.setEnabled(False)
            self.collection_path = None  # Remove collection path to make sure nothing wonky happens

    def browse_shelf_path(self):
        """Creates a browse session so the user can locate a shelf file"""
        # Get the path to the shelf
        (filename, ext) = QFileDialog.getOpenFileName(None, "Locate Shelf Files",
                                                      self.shelf_working_path, "Shelf files (*.bak *.dat *.dir)")
        # todo add handle for canceling the load
        assert filename[-4:] in {'.bak', '.dat', '.dir'}, "Selected file not supported for loading."
        self.shelf_path = filename[:-4]
        # Update working_path to save user preference
        self.shelf_working_path = path.dirname(filename)
        # Update line edit
        self.line_query_path.setPlainText(self.shelf_path)
        # Enable load button
        self.butt_load_query_path.setEnabled(True)
        self.butt_load_query_path.setText("Load")
        # Refresh GUI
        self.refresh()

    def load_shelf_file(self):
        """Loads a shelf file containing the queries and processes it for viewing"""
        # Load shelf data
        print("Loading shelf file:", self.shelf_path)
        self.queries = load_query_list(self.shelf_path)
        self.query_list = process_query_list(self.queries)
        # Disable load button
        self.butt_load_query_path.setEnabled(False)
        self.butt_load_query_path.setText("Loaded")
        # Set combobox
        self.build_combo_box_entries()
        self.update_query_selection_combo()
        # Refresh GUI
        self.refresh()

    def browse_and_load(self):
        """Utility function for menu bar 'load'"""
        self.browse_shelf_path()
        self.load_shelf_file()

    def check_query_path(self):
        """ """
        temp_path = self.line_query_path.toPlainText()
        if temp_path and (path.exists(temp_path) or path.exists(temp_path+'.dir')):
            self.butt_load_query_path.setEnabled(True)
            self.shelf_path = self.line_query_path.toPlainText()
            self.shelf_working_path = self.shelf_path
        else:
            self.butt_load_query_path.setEnabled(False)
            self.shelf_path = None  # Remove shelf path to make sure nothing wonky happens

    def refresh(self):
        """Refreshes the UI and verifies that GUI elements are accurate."""
        pass

    def build_combo_box_entries(self):
        """ """
        entries = []
        for query in self.queries:
            label = [query.UUID, query.phrase]
            flag_list = []
            try:
                flags = query.flags
                order = ['case-sensitive', 'whole-word', 'constituents', 'plurals', 'special-delims']
                acronyms = ['cs', 'w', 'cn', 'p', 'd']
                for f_ind, flag in enumerate(order):
                    if flag in flags and flags[flag]:
                        flag_list.append(acronyms[f_ind])
            except AttributeError:
                pass
            if flag_list:
                label.append('[' + ', '.join(flag_list) + ']')
            entries.append(', '.join(label))
        self.formatted_queries = entries

    def update_query_selection_combo(self):
        """ """
        # Query Selection Combo Box
        for index in range(max(len(self.formatted_queries), self.combo_query.count())):
            if index > len(self.formatted_queries) - 1:
                self.combo_query.removeItem(index)
            else:
                if index <= self.combo_query.count() - 1:
                    self.combo_query.setItemText(index, self.formatted_queries[index])
                else:
                    self.combo_query.addItem(self.formatted_queries[index])

    def set_query_combo(self):
        """Set attribute for identifying the selected query"""
        self.selected_query = self.combo_query.currentIndex()
        if self.combo_query.currentIndex() >= 0:
            self.butt_apply_query.setEnabled(True)

    def clear_query_box(self):
        self.combo_query.setCurrentIndex(-1)

    def process_configuration(self):
        """ """
        # ========================================================================================
        self.prog_bar.setRange(0, 4)
        self.butt_process_collection_processing.setEnabled(False)
        self.application.processEvents()
        # ========================================================================================
        self.prog_label.setText("Initializing Collection object...")
        self.application.processEvents()
        # ------------------------------------
        LANGUAGE = "english"
        stemmer = Stemmer(LANGUAGE)
        summarizer = LexSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
        token = Tokenizer(LANGUAGE)
        term_frequency_threshold = 0.5
        #
        self.collection_path = self.line_collection_path.toPlainText()  # make sure the collection path is updated
        self.cobj = Collection(self.collection_path)
        # -------------------------------------
        self.prog_bar.setValue(2)
        # ========================================================================================
        self.prog_label.setText("Processing collection...")
        self.application.processEvents()
        self.cobj.process_collection()
        self.prog_bar.setValue(3)
        # ========================================================================================
        self.prog_label.setText("Generating metadata...")
        self.application.processEvents()
        self.cobj.generate_metadata(summarizer, token, term_frequency_threshold)
        self.prog_bar.setValue(4)
        # ========================================================================================
        self.prog_label.setText("Done!")
        self.butt_process_collection_processing.setEnabled(True)
        self.butt_apply_query.setEnabled(True)

    def apply_query(self):
        """
         Executes after the 'Generate Results' button is pressed.
        """
        LANGUAGE = "english"
        stemmer = Stemmer(LANGUAGE)
        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
        token = Tokenizer(LANGUAGE)

        class Results(object):
            """Dummy object to pass to results functions"""
            def __init__(self):
                self.summary = None
                self.words = None

            def set_summary(self, summary):
                self.summary = summary

            def set_words(self, words):
                self.words = words

        if self.cobj:
            print("Collection object loaded.")

        else:
            from milnlp.collection.collection import Collection, get_items
            self.cobj = Collection(self.collection_path)
            self.cobj.flist, self.cobj.dlist = get_items(self.collection_path, set(), {self.collection_path: 0})

        # Build composite document
        if self.radio_full.isChecked():
            method = "full"
        else:
            method = "reduced"

        try:
            buffer_size = self.spin_sentence_buffer.value()

            if self.combo_query.currentIndex() > -1:  # execute for query
                query_to_apply = self.queries[self.combo_query.currentIndex()]
                purge_matches(query_to_apply)
                self.document, self.matches = self.cobj.create_composite_doc_from_query_object(query_to_apply,
                                                                                               token,
                                                                                               method=method,
                                                                                               buffer_size=buffer_size)
                print(f"Using method '{method}' results in: ", self.document)

            else:  # execute for entire sub-collection
                from sumy.models.dom import ObjectDocumentModel
                from ..collection.collection import reparser

                files = [file[:-4]+'.txt' for file in self.cobj.flist]
                parsed_docs = reparser(files, token, method='full')
                composite_doc_paragraphs = []
                for d_parser in parsed_docs.values():
                    composite_doc_paragraphs.extend(d_parser.document.paragraphs)
                self.document, self.matches = ObjectDocumentModel(composite_doc_paragraphs), None

            self.results = Results()

            # Generate message box to confirm the user wants a summary to be generated
            msgBox = QMessageBox()  # todo add window name
            msgBox.setText(f"The composite document has been created. It contains {len(self.document.sentences)} "
                           f"sentences. Do you want to summarize the document?")
            msgBox.setInformativeText("")
            msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgBox.setDefaultButton(QMessageBox.Yes)
            ret = msgBox.exec_()
            if ret == QMessageBox.No:
                self.write_matches_panel()
                return 0  # cancel the task

            # Generate summary  # todo # sentences not working
            reduced_summary = self.cobj.summarize_composite(self.document, summarizer, self.num_sentences)
            self.results.set_summary(reduced_summary)

            # Generate key words/phrases
            text = doc_to_text(self.document)
            words = dict(score_keyphrases_by_textrank(text, self.num_keywords))
            self.results.set_words(words)

            # Display results
            self.write_matches_panel()
            self.print_results(method='collection')
            self.write_results_panel(method='collection')
            self.tab_widget.setCurrentIndex(2)
        except TypeError:
            # No matches for query, therefore different return route
            msg_box = QMessageBox()
            msg_box.setText('The query returned no matches for the specified collection.')
            msg_box.exec_()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     SINGLE DOCUMENT TAB/PANEL BELOW
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def set_sentences(self):
        """ """
        self.num_sentences = self.spin_num_sentences.value()
        self.spin_num_sentences_collection.setValue(self.num_sentences)

    def set_words(self):
        """ """
        self.num_keywords = self.spin_num_words.value()
        self.spin_num_words_collection.setValue(self.num_keywords)

    def enable_summary_button(self):
        """ """
        file_path = self.line_file_path.toPlainText()
        if file_path and path.exists(file_path):
            self.butt_summarize.setEnabled(True)
            self.file_path = file_path
        else:
            self.butt_summarize.setEnabled(False)

    def browse_file_path(self):
        """Creates a browse session so the user can locate a file path"""
        # Get the path to file
        (self.file_path, ext) = QFileDialog.getOpenFileName(None, "Locate File",
                                                            self.working_path,
                                                            "File: (*.pdf)")
        # todo add handle for canceling the load
        # Update working_path to save user preference
        self.working_path = self.file_path
        # Update line edit
        self.line_file_path.setPlainText(self.file_path)

    def apply_summary(self):
        """ """
        results = SingleDocSummarizer(Tokenizer, Summarizer)
        results.process_document(self.file_path,
                                 num_sentences=self.num_sentences,
                                 num_keywords=self.num_keywords)
        self.results = results
        self.print_results()
        self.write_results_panel()
        self.tab_widget.setCurrentIndex(2)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     COMMON PANEL METHODS BELOW
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def enable_save_results_button(self):
        """ """
        if self.results_text.toPlainText():
            self.butt_save_results.setEnabled(True)
        else:
            self.butt_save_results.setEnabled(False)

    def write_results_panel(self, method='single'):
        """method:
             'single': single document
             'collection': collection or sub-collection of documents
        """
        text = ''
        text = text + "==================================\n"
        if method == 'single':
            text = text + f"File path: {self.file_path}\n"
        else:
            text = text + f"Collection path: {self.collection_path}\n"
            text = text + "\nQueries:\n"
            for ii, query in enumerate(self.formatted_queries):
                if ii == self.combo_query.currentIndex():
                    text = text + f"->\t{ii+1}) {query}\n"
                else:
                    text = text + f"\t{ii+1}) {query}\n"
        text = text + f"\n# Summary Sentences: {self.num_sentences}\n"
        text = text + f"# Key Words/Phrases: {self.num_keywords}\n\n"
        text = text + "==================================\n" \
                      "Summary:\n==================================\n"
        for sentence in self.results.summary:
            text = text + f" *  {sentence}\n\n"
        text = text + "\n==================================\n" \
                      "Key Words/Phrases: \n==================================\n"
        for ii, item in enumerate(self.results.words.items()):
            if ii >= self.num_keywords:
                break
            text = text + f"{'%.6f'%item[1]},\t{item[0]}\n"
        self.results_text.setPlainText(text)

    def print_results(self, method='single'):
        """Print formatted results to console."""
        print("==================================")
        if method == 'single':
            print(f"File path: {self.file_path}")
        else:
            print(f"Collection path: {self.collection_path}")
            print("\nQueries:")
            for ii, query in enumerate(self.formatted_queries):
                if ii == self.combo_query.currentIndex():
                    print(f"->\t{ii+1}) {query}")
                else:
                    print(f"\t{ii+1}) {query}")
        print(f"\n# Summary Sentences: {self.num_sentences}")
        print(f"# Key Words/Phrases: {self.num_keywords}\n")
        print("==================================\n"
              "Summary:\n"
              "==================================\n")
        for sentence in self.results.summary:
            print(f" *  {sentence}\n")
        print("\n==================================\n"
              "Key Words/Phrases: \n"
              "==================================\n")
        for ii, item in enumerate(self.results.words.items()):
            if ii >= self.num_keywords:
                break
            print(f"{'%.6f'%item[1]},\t{item[0]}")

    def write_results(self):
        """Write formatted results to file."""
        import webbrowser

        if self.collection_path != getcwd():
            save_path = self.collection_path
        else:
            save_path = self.working_path
        (save_path, ext) = QFileDialog.getSaveFileName(None, "Specify File to Save",
                                                       save_path, "Results file (*.results)")
        if save_path:
            with open(save_path, 'w') as ofile:
                print("\nWriting results to:", save_path)
                ofile.write(self.results_text.toPlainText())
                print("Done!")
            webbrowser.open(save_path)

    def write_matches_panel(self):
        """Simple result to display the matching files/pages"""
        if self.combo_query.currentIndex() > -1:
            text = self.recursive_level_check(list(self.matches.keys()), self.matches)
        else:
            text = ""  # erase any text to be sure
        self.matches_text.setPlainText(text)

    def recursive_level_check(self, files, file_dict, level=1, text=''):
        sep = '\\'
        segments = [file.split(sep) for file in files]  # path split into segments
        groups = {}
        printed = {}
        for ii, segment in enumerate(segments):
            if len(segment) == level:
                key = sep.join(segment[:level - 1])
                if key not in printed:
                    printed[key] = True
                    text += '\n'+key+sep+'\n'
                text += ' '+u"\u251C"+'- '+str(segment[-1])+'\n'
                text += '     Page matches:'+', '.join([str(item+1) for item in file_dict[files[ii]]])+'\n'
            elif len(segment) > level:
                key = sep.join(segment[0:level])
                if key not in groups:
                    groups[key] = {files[ii]}
                else:
                    groups[key].update({files[ii]})

        # Recursive call if not exhausted
        if groups:
            for group in groups.values():
                text = self.recursive_level_check(list(group), file_dict, level=level + 1, text=text)

        return text

#
#  Application Below  ----------------------------------------
#


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loc = path.dirname(__file__)
    if not loc:
        loc = getcwd()
    form = Form(loc + '\\' + "summary_tool.ui", app)
    sys.exit(app.exec_())
