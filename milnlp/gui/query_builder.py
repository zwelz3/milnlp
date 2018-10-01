# main.py
import sys
import shelve
import subprocess
from os import getcwd, path, remove
#
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtWidgets import QPushButton, QRadioButton, QLineEdit, QCheckBox, QComboBox
from PySide2.QtWidgets import QAction, QGroupBox, QFileDialog
from PySide2.QtCore import QFile, QObject, QPersistentModelIndex
#
from milnlp.collection.topic_model import SimpleQuery, ComplexQuery
from milnlp.gui.utils import load_query_list, process_query_list
from milnlp.gui.widgets import PandasModel


def open_summary_tool():
    """Opens the query builder tool from within the summary tool
    TODO fix on export implementation"""
    if not path.exists("summary_tool.py"):
        print("The summary tool is not installed.")
        return 1
    subprocess.Popen("python summary_tool.py")  #todo add execute paramters to load file from QB


def run():
    app = QApplication(sys.argv)
    loc = path.dirname(__file__)
    form = Form(loc + '\\' + "query_builder.ui", app)
    sys.exit(app.exec_())


class Form(QObject):
    """Basic form class for loading uifile"""
    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)
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
        self.save_file_path = None
        self.shelf_path = None
        self.working_path = getcwd()   # contains the working shelf path (updates for multiple saves/loads)
        self.query_list = []           # visual list for the GUI
        self.queries = []              # shelve object list
        self.table_model = None        # table object displaying the query_list
        self.sq_flags = {
            'case-sensitive': False,
            'whole-word': False,
            'special-delims': False,
            'plurals': False,
            'constituents': False,
        }  # dictionary containing flag states
        self.cq_left = None   # selection of complex query
        self.cq_right = None  # selection of complex query
        self.hidden = []      # list of hidden rows

        # ================================
        # Locate and bind window children
        # ================================
        # menuBar -> menuTools  todo export queries (no matches retained)
        action_save = self.window.findChild(QAction, 'actionSaveQL')
        action_save.triggered.connect(self.save_file)
        action_save_as = self.window.findChild(QAction, 'actionSaveAsQL')
        action_save_as.triggered.connect(self.save_as_file)
        action_load = self.window.findChild(QAction, 'actionLoadQL')
        action_load.triggered.connect(self.load_file)
        action_refresh = self.window.findChild(QAction, 'actionRefresh')
        action_refresh.triggered.connect(self.refresh)
        action_export = self.window.findChild(QAction, 'actionExportST')
        action_export.triggered.connect(open_summary_tool)

        # QueryList -> QGroupBox
        butt_remove_query = self.window.findChild(QPushButton, 'removeQueryButton')
        butt_remove_query.clicked.connect(self.remove_query)
        butt_hide_row = self.window.findChild(QPushButton, 'hideRowButton')
        butt_hide_row.clicked.connect(self.hide_row)
        butt_show_rows = self.window.findChild(QPushButton, 'showRowsButton')
        butt_show_rows.clicked.connect(self.show_rows)
        butt_clear_queries = self.window.findChild(QPushButton, 'clearQueriesButton')
        butt_clear_queries.clicked.connect(self.clear_queries)

        # SimpleQuery -> QGroupBox
        #  -Phrase
        self.line_phrase = self.window.findChild(QLineEdit, 'phraseEdit')
        #  -Check Boxes
        self.check_case = self.window.findChild(QCheckBox, 'caseSenseCheck')
        self.check_word = self.window.findChild(QCheckBox, 'wholeWordCheck')
        self.check_delim = self.window.findChild(QCheckBox, 'specDelimsCheck')
        self.check_plural = self.window.findChild(QCheckBox, 'pluralsCheck')
        self.check_const = self.window.findChild(QCheckBox, 'constituentsCheck')
        #  -Button
        butt_simple = self.window.findChild(QPushButton, 'addSimpleButton')
        butt_simple.clicked.connect(self.add_simple_query)

        # ComplexQuery -> QGroupBox
        #  -Combo Boxes
        self.cq_combo_left = self.window.findChild(QComboBox, 'cqBoxLeft')
        self.cq_combo_left.currentIndexChanged.connect(self.set_cq)
        self.cq_combo_right = self.window.findChild(QComboBox, 'cqBoxRight')
        self.cq_combo_right.currentIndexChanged.connect(self.set_cq)
        #  -Radio
        self.union_radio = self.window.findChild(QRadioButton, 'cqRadioUnion')
        self.union_radio.setChecked(True)  # union by default
        self.intersect_radio = self.window.findChild(QRadioButton, 'cqRadioIntersection')
        #  -Button
        butt_complex = self.window.findChild(QPushButton, 'addComplexButton')
        butt_complex.clicked.connect(self.add_complex_query)

        # ========
        #   Show
        # ========
        self.window.show()

    #
    #     METHODS BELOW   ---------------------------------------
    #

    def save_file(self):
        """
        Note: Assumes the path is already set from loading.
        todo add 'Save-As' option
        todo gray out option until state of queries has changed
        Note!!!! The shelf overwrites entries, but does not alter others. I.e. if the GUI only has 1 query, but the
        shelf file has 3, the two will still persist in the file. todo change this behavior to something smarter
        """
        if self.queries:
            # todo likely replace old file (i.e. delete then write) because of shelf issues with overwriting
            with shelve.open(self.save_file_path, 'c') as shelf:
                for instance in self.queries:
                    shelf[instance.UUID] = instance
        else:
            print("INFO: There are no queries to save")

    def save_as_file(self):
        """ """
        if self.queries:
            (save_path, ext) = QFileDialog.getSaveFileName(None, "Specify File to Save",
                                                          self.working_path, "Shelf file (*.dat)")
            save_file = save_path.split('/')[-1].split('.')
            if len(save_file) == 2:
                assert save_file[-1] == 'dat', "ERROR: please use '.dat' extension or none."
                self.save_file_path = save_path[:-4]
            elif len(save_file) == 1:
                self.save_file_path = save_path
            # todo replace file if exists (request pops up, but doesn't so anything)
            if path.exists(save_path):
                print("INFO: removing old file to ensure accurate replacement.")
                try:
                    remove(self.save_file_path + '.dat')
                    remove(self.save_file_path + '.bak')
                    remove(self.save_file_path + '.dir')
                except FileNotFoundError:  # i.e. one of the files has already been removed
                    pass
            with shelve.open(self.save_file_path, 'c') as shelf:
                for instance in self.queries:
                    shelf[instance.UUID] = instance
            # todo enable save option now that save-as is complete
        else:
            print("INFO: There are no queries to save")

    def load_file(self):
        """Loads a shelf file containing the queries and processes it for viewing"""
        # Get the path to the shelf
        (filename, ext) = QFileDialog.getOpenFileName(None, "Locate Shelf Files",
                                                      self.working_path, "Shelf files (*.bak *.dat *.dir)")
        # todo add handle for canceling the load
        assert filename[-4:] in {'.bak', '.dat', '.dir'}, "Selected file not supported for loading."
        self.shelf_path = filename[:-4]
        # Load shelf data
        print("Loading shelf file:", self.shelf_path)
        self.queries = load_query_list(self.shelf_path)
        self.query_list = process_query_list(self.queries)
        # Add shelf data to table model and inject into view
        self.table_model = PandasModel(self.query_list)
        self.refresh()
        # Update working_path to save user preference
        self.working_path = path.dirname(filename)  # Note* using filename not shelf_path which is custom for shelf
        # Update simple/complex query classes with latest UUID position
        temp_dict = {}
        for UUID in [item.UUID for item in self.queries]:
            qtype, index = UUID.split('_')
            if qtype in temp_dict:
                temp_dict[qtype] = max(temp_dict[qtype], int(index))
            else:
                temp_dict[qtype] = int(index)
        assert "SQ" in temp_dict, "You are attempting to load a corrupt file."
        SimpleQuery.UUID_INDEX = temp_dict["SQ"]+1
        try:
            ComplexQuery.UUID_INDEX = temp_dict["CQ"] + 1
        except KeyError:
            pass  # Complex query not on shelf

    def clear_queries(self):
        """Clears the queries from their relevant objects and GUI elements"""
        self.query_list = []
        self.queries = []
        self.table_model = None
        self.window.tableView.reset()
        self.refresh(combo=False)
        # Clear combobox
        self.cq_combo_left.clear()
        self.cq_combo_right.clear()
        # Reset classes
        SimpleQuery.UUID_INDEX = 1
        ComplexQuery.UUID_INDEX = 1

    def refresh(self, combo=True):
        """Refreshes the UI and verifies that GUI elements are accurate."""
        self.window.tableView.setModel(self.table_model)
        self.window.tableView.resizeColumnsToContents()
        if combo:
            # Complex Query Combo Boxes
            assert self.cq_combo_left.count() == self.cq_combo_right.count(), \
                "ERROR: combobox lists are out of alignment."
            for index in range(max(len(self.queries), self.cq_combo_left.count())):
                if index > len(self.queries)-1:
                    self.cq_combo_left.removeItem(index)
                    self.cq_combo_right.removeItem(index)
                else:
                    if index <= self.cq_combo_left.count()-1:
                        self.cq_combo_left.setItemText(index, self.queries[index].UUID)
                        self.cq_combo_right.setItemText(index, self.queries[index].UUID)
                    else:
                        self.cq_combo_left.addItem(self.queries[index].UUID)
                        self.cq_combo_right.addItem(self.queries[index].UUID)

    def cb_sq_flags(self):
        """Flip flag boolean on click
        CheckBox -> Simple Query -> Flags
        todo switch with map
        """
        for key in self.sq_flags:
            if key == 'case-sensitive':
                self.sq_flags[key] = bool(self.check_case.checkState())
            elif key == 'whole-word':
                self.sq_flags[key] = bool(self.check_word.checkState())
            elif key == 'special-delims':
                self.sq_flags[key] = bool(self.check_delim.checkState())
            elif key == 'plurals':
                self.sq_flags[key] = bool(self.check_plural.checkState())
            elif key == 'constituents':
                self.sq_flags[key] = bool(self.check_const.checkState())
            else:
                print(f"ERROR: flag {key} has not been bound to an attribute yet. ")

    def add_simple_query(self):
        """Create simple query object from 'Simple Query Builder' QGroupBox"""
        # Collect phrase and remove leading/trailing spaces
        phrase = self.line_phrase.text().lstrip().rstrip()
        if not phrase:
            return None
        # Update flags w/ check_box states
        self.cb_sq_flags()
        # Build simple query object
        sq_inst = SimpleQuery(phrase)
        sq_inst.update_flags(self.sq_flags)
        self.queries.append(sq_inst)
        self.query_list = process_query_list(self.queries)  # todo replace with only having to append newest
        self.table_model = PandasModel(self.query_list)     # todo add method for appending row to model
        self.refresh()

    def set_cq(self):
        """Set attributes for identifying the selected queries"""
        self.cq_left = self.cq_combo_left.currentIndex()
        self.cq_right = self.cq_combo_right.currentIndex()

    def add_complex_query(self):
        """ """
        # Make sure queries are set
        if self.cq_left is None or self.cq_right is None:
            print("INFO: Using the default selected queries.")
            self.set_cq()
        # Get method from radio buttons
        if self.union_radio.isChecked():
            method = 'union'
        elif self.intersect_radio.isChecked():
            method = 'intersection'
        # Build the complex query
        key_list = [self.queries[self.cq_left].UUID, self.queries[self.cq_right].UUID]
        cq_inst = ComplexQuery(key_list, method, object_list=self.queries)
        self.queries.append(cq_inst)
        self.query_list = process_query_list(self.queries)  # todo replace with only having to append newest
        self.table_model = PandasModel(self.query_list)  # todo add method for appending row to model
        self.refresh()

    def remove_query(self):
        """Deletes a query from the form completely."""
        index_list = []
        for model_index in self.window.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)
        # Remove from table model, query_list, and queries
        for index in sorted(index_list, reverse=True):
            del self.queries[index.row()]
            self.query_list.drop(self.query_list.index[[index.row()]], inplace=True)
        # Refresh
        self.window.tableView.reset()
        self.refresh()

    def hide_row(self):
        """Hides a row (or multiple rows)."""
        index_list = []
        for model_index in self.window.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)
        # Remove from table model, query_list, and queries
        for index in sorted(index_list, reverse=True):
            self.window.tableView.setRowHidden(index.row(), True)
            self.hidden.append(index)
        # todo set enabled 'show all rows" button now that rows are hidden
        # Refresh
        self.window.tableView.reset()
        self.refresh()

    def show_rows(self):
        """Shows all rows that were previously hidden."""
        if self.hidden:
            for index in self.hidden:
                self.window.tableView.setRowHidden(index.row(), False)
        # todo set to inactive once all rows are visible
        # Refresh
        self.window.tableView.reset()
        self.refresh()

    @staticmethod
    def phw():
        """Tester function for GUI elements"""
        print("Hello, World!")

#
#  Application Below  ----------------------------------------
#


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loc = path.dirname(__file__)
    if not loc:
        loc = getcwd()
    form = Form(loc + '\\' + "query_builder.ui", app)
    sys.exit(app.exec_())
