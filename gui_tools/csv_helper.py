print("Importing...")
import sys
import numpy as np
import skimage.io

from pyqtgraph.Qt import QtWidgets, QtGui
import pyqtgraph as pg


class CSVHelper(QtWidgets.QWidget):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filename = filename
        self.setWindowTitle(filename)
        self.setLayout(self.make_layout())

    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        self.plot = pg.PlotWidget()
        self.plotItem = self.plot.getPlotItem()
        layout.addWidget(self.plot, 0, 0)

        x, y = np.genfromtxt(self.filename, delimiter=',', unpack=True)

        self.plotItem.plot(x, y)

        return layout


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "file"

    print("Building app...")
    app = QtWidgets.QApplication([])
    window = CSVHelper(filename)

    window.show()

    app.exec()
