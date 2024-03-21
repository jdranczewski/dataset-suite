import puzzlepiece as pzp
from qtpy import QtWidgets

import os, sys

class PretendPuzzle:
    debug = True

class FileView(pzp.Piece):
    def __init__(self, override_param_layout=True, *args, **kwargs):
        if override_param_layout:
            self._param_layout = self.param_layout
            self.param_layout = lambda: QtWidgets.QVBoxLayout()
            self._action_layout = self.action_layout
            self.action_layout = lambda: QtWidgets.QVBoxLayout()
        super().__init__(
            PretendPuzzle(),
            custom_horizontal=False,
            *args, **kwargs
        )

    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.label)
        return layout

    def set_file(self, filename):
        self.label.setText(filename)

class FileButton(QtWidgets.QRadioButton):
    def __init__(self, folder, filename, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)

        self.path = os.path.join(folder, filename)
        self.filename = os.path.basename(filename)

class FilesViewer(QtWidgets.QWidget):
    def __init__(self, filename, viewer=FileView, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.setWindowTitle(filename)
        self.file_view = viewer(filename)
        self.setLayout(self.make_layout(filename))

    def make_layout(self, filename):
        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.file_view, 0, 0, 3, 1)

        scroll_container = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        for folder, file in self._list_files(filename):
            button = FileButton(folder, file)
            scroll_layout.addWidget(button)
            button.clicked.connect(self._folder_button_clicked)
            if button.path == filename:
                button.click()

        scroll_widget.setLayout(scroll_layout)
        scroll_container.setWidget(scroll_widget)

        pad = 0
        if len(self.file_view.params):
            layout.addLayout(self.file_view._param_layout(), 0, 1)
            pad += 1
        if len(self.file_view.params):
            layout.addLayout(self.file_view._action_layout(), pad, 1)
            pad += 1
        layout.addWidget(scroll_container, pad, 1, 3-pad, 1)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)

        return layout
    
    def _list_files(self, filename):
        folder = os.path.dirname(filename)
        extension = filename.split('.')[-1]
        if not len(folder):
            folder = '.'
        for file in os.listdir(folder):
            if '.' + extension in file:
                yield folder, file
    
    def _folder_button_clicked(self):
        self.setWindowTitle(self.sender().filename)
        self.file_view.set_file(self.sender().path)


# This will eventually come to puzzlepiece, but putting it here for now
class DataGrid(QtWidgets.QWidget):
    def __init__(self, row_class):
        super().__init__()
        self._tree = QtWidgets.QTreeWidget()
        self._row_class = row_class
        row_example = row_class()
        self._tree.setHeaderLabels(('ID', *row_example.params.keys(), 'actions'))
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._tree)
        self.setLayout(layout)
        self.rows = []
        self._items = []
        self._root = self._tree.invisibleRootItem()
        self._slots = {}

    def add_row(self, **kwargs):
        item = QtWidgets.QTreeWidgetItem(self._tree, (str(len(self.rows)),))
        row = self._row_class()
        row._populate_item(self._tree, item)
        self.rows.append(row)
        self._items.append(item)
        for key in kwargs:
            row.params[key].set_value(kwargs[key])
        for param_name in self._slots:
            for slot in self._slots[param_name]:
                row.params[param_name].changed.connect(slot)
        return row

    def remove_row(self, id):
        self._root.removeChild(self._items[id])
        del self._items[id]
        del self.rows[id]
        for i in range(len(self.rows)):
            self._items[i].setText(0, str(i))

    def get_index(self, row):
        return self.rows.index(row)

    def clear(self):
        self._tree.clear()
        self.rows = []
        self._items = []

    def add_changed_slot(self, param_name, function):
        if param_name in self._slots:
            self._slots[param_name].append(function)
        else:
            self._slots[param_name] = [function]
        for row in self.rows:
            row.params[param_name].changed.connect(function)

class Row:
    def __init__(self):
        self.params = {}
        self.actions = {}
        self.define_params()
        self.define_actions()
        for key in self.params:
            self.params[key]._main_layout.removeWidget(self.params[key].label)
        
    def define_params(self):
        pass

    def define_actions(self):
        pass

    def elevate(self):
        pass

    def _populate_item(self, tree, item):
        for i, key in enumerate(self.params):
            tree.setItemWidget(item, i+1, self.params[key])
        tree.setItemWidget(item, i+2, self._action_buttons())

    def _action_buttons(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        widget.setLayout(layout)
        
        visible_actions = [key for key in self.actions if self.actions[key].visible]
        for i, key in enumerate(visible_actions):
            button = QtWidgets.QPushButton(key)
            button.clicked.connect(lambda x=False, _key=key: self.actions[_key]())
            layout.addWidget(button)
        return widget
        
    def __iter__(self):
        for key in self.params:
            yield key
    
    def __getitem__(self, key):
        return self.params[key]
    
    def __contains__(self, item):
        return item in self.params
    

class FileRow(Row):
    def define_params(self):
        pzp.param.readout(self, 'filename')(None)

    def define_actions(self):
        @pzp.action.define(self, "Close")
        def close(self):
            self.dialog.accept()


class ManyFilesViewer(QtWidgets.QWidget):
    def __init__(self, viewer=FileView, *args, **kwargs):
        super().__init__(None, *args, **kwargs)
        self.setWindowTitle("Files viewer")
        self.file_viewer = viewer
        self.setAcceptDrops(True)
        self.setLayout(self.make_layout())

    def make_layout(self):
        layout = QtWidgets.QGridLayout()
        self.data_grid = DataGrid(FileRow)
        layout.addWidget(self.data_grid, 0, 0)
        return layout
    
    def add_file(self, filename):
        dialog = QtWidgets.QDialog(self)
        layout2 = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout2)

        file_view = self.file_viewer(override_param_layout=False)
        file_view.setStyleSheet("QGroupBox {border:0;}")
        layout2.addWidget(file_view)

        # Display the dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        file_view.set_file(filename)

        # Add a row
        row = self.data_grid.add_row(filename=filename)
        row.dialog = dialog

        # Remvoe the row when dialog closed
        def remove():
            self.data_grid.remove_row(self.data_grid.get_index(row))
        dialog.finished.connect(remove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_file(event.mimeData().urls()[0].path())
        event.acceptProposedAction()
    
if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "test.py"

    app = QtWidgets.QApplication([])
    main = FilesViewer(filename)
    main.show()
    app.exec()