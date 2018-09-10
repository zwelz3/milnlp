from PySide2.QtCore import Qt, QAbstractTableModel


class BasicTableModel(QAbstractTableModel):
    def __init__(self, data, header, *args, parent=None):
        super(BasicTableModel, self).__init__()
        self.data = data
        self.header = header

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.data[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.data = sorted(self.data,
            key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.data.reverse()
        self.emit(SIGNAL("layoutChanged()"))


class PandasModel(QAbstractTableModel):
    """
    Class to populate a table view with a pandas DataFrame
    """
    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def removeRow(self, index):
        self._data.drop(self._data.index[[index]], inplace=True)
        return None
