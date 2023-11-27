import sys
import numpy as np
import datasets as ds

from pyqtgraph.Qt import QtWidgets, QtGui
import pyqtgraph as pg


class HSViewer(QtWidgets.QWidget):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filename = filename
        self.setWindowTitle(filename)
        self.setLayout(self.make_layout())

    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        self.gl = pg.GraphicsLayoutWidget()
        layout.addWidget(self.gl, 0, 0)

        self._plots = []
        self._images = []
        for i in range(3):
            plot = self.gl.addPlot(0, i)
            image = pg.ImageItem(border='w', axisOrder='row-major')
            plot.addItem(image)

            self._plots.append(plot)
            self._images.append(image)

        self.dataset = ds.load(self.filename)
        self.dataset._raw -= self.dataset.metadata['background']
        self._images[0].setImage(np.amax(self.dataset.raw, 2))

        line_pos = pg.InfiniteLine(0, 0, movable=True)
        line_pos.sigPositionChanged.connect(self._updated_pos)
        self._plots[0].addItem(line_pos)

        line_wl = pg.InfiniteLine(0, 90, movable=True)
        line_wl.sigPositionChanged.connect(self._updated_wl)
        self._plots[1].addItem(line_wl)

        return layout

    def _updated_pos(self, line):
        self._images[1].setImage(self.dataset.take_raw(pos=int(line.value())))

    def _updated_wl(self, line):
        self._images[2].setImage(self.dataset.take_raw(wl=int(line.value())))


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'file'

    print("Building app...")
    app = QtWidgets.QApplication([])
    window = HSViewer(filename)

    window.show()

    app.exec()
