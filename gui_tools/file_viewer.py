import puzzlepiece as pzp
from qtpy import QtWidgets

import os, sys

class PretendPuzzle:
    debug = True

class FileView(pzp.Piece):
    def __init__(self, *args, **kwargs):
        self._param_layout = self.param_layout
        self.param_layout = lambda: QtWidgets.QVBoxLayout()
        super().__init__(PretendPuzzle(), *args, **kwargs)

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
        self.file_view = viewer(filename)
        self.setLayout(self.make_layout(filename))

    def make_layout(self, filename):
        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.file_view, 0, 0, 2, 1)

        scroll_container = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        folder = os.path.dirname(filename)
        extension = filename.split('.')[-1]
        if not len(folder):
            folder = '.'
        for file in os.listdir(folder):
            if '.' + extension in file:
                button = FileButton(folder, file)
                scroll_layout.addWidget(button)
                button.clicked.connect(self._folder_button_clicked)
                if button.path == filename:
                    button.click()

        scroll_widget.setLayout(scroll_layout)
        scroll_container.setWidget(scroll_widget)

        if len(self.file_view.params):
            layout.addLayout(self.file_view._param_layout(), 0, 1)
            layout.addWidget(scroll_container, 1, 1)
        else:
            layout.addWidget(scroll_container, 0, 1, 2, 1)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)

        return layout
    
    def _folder_button_clicked(self):
        self.file_view.set_file(self.sender().path)
    
if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "test.py"

    app = QtWidgets.QApplication([])
    main = FilesViewer(filename)
    main.show()
    app.exec()