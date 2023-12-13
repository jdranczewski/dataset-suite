import file_viewer
import puzzlepiece as pzp
from qtpy import QtWidgets

import pyqtgraph as pg
import datasets as ds
import numpy as np

import sys, os

class HSView(file_viewer.FileView):
    def __init__(self, *args, **kwargs):
        self._get_coordinates()
        super().__init__(*args, **kwargs)

    def define_params(self):
        pzp.param.readout(self, 'wavelength', True, '{:.2f}nm')(None)
        pzp.param.checkbox(self, 'overlay', 1)(None)

    def custom_layout(self):
        layout = QtWidgets.QGridLayout()

        self.gl = pg.GraphicsLayoutWidget()
        layout.addWidget(self.gl, 0, 0)

        self._plots = []
        self._images = []
        self._lines = []
        self._net_lines = []
        self._controls = {}

        # Plot 0
        plot = self.gl.addPlot(0, 0)
        image = pg.ImageItem(border='w')
        plot.addItem(image)
        self._controls['target'] = pg.TargetItem((0, 0))
        self._controls['space_line'] = pg.InfiniteLine(0, 90, pen=(255, 0, 0, 100))
        plot.addItem(self._controls['target'])
        plot.addItem(self._controls['space_line'])

        self._net_lines.append(plot.plot([0], [0], pen=(0, 0, 255, 100)))
        self._plots.append(plot)
        self._images.append(image)

        # Plot 1
        plot = self.gl.addPlot(0, 1)
        plot.setYLink(self._plots[0])
        image = pg.ImageItem(border='w', axisOrder='row-major')
        plot.addItem(image)
        self._controls['space_line_2'] = pg.InfiniteLine(0, 0, pen=(255, 0, 0, 100))
        self._controls['wl_line'] = pg.InfiniteLine(0, 90, movable=True)
        plot.addItem(self._controls['space_line_2'])
        plot.addItem(self._controls['wl_line'])

        self._plots.append(plot)
        self._images.append(image)

        # Plot 2
        plot = self.gl.addPlot(1, 1)
        self._plots.append(plot)
        self._lines.append(plot.plot((0,), (0,)))
        plot.setXLink(self._plots[1])
        self._controls['wl_line_2'] = pg.InfiniteLine(0, 90, pen=(255, 0, 0, 100))
        plot.addItem(self._controls['wl_line_2'])

        # Plot 3
        plot = self.gl.addPlot(1, 0)
        image = pg.ImageItem(border='w')
        plot.addItem(image)
        self._net_lines.append(plot.plot([0], [0], pen=(0, 0, 255, 100)))
        plot.setXLink(self._plots[0])
        plot.setYLink(self._plots[0])
        self._controls['target_2'] = pg.TargetItem((0, 0), movable=False, pen=(255, 0, 0, 100))
        plot.addItem(self._controls['target_2'])

        self._plots.append(plot)
        self._images.append(image)

        # Signalling
        self._controls['target'].sigPositionChanged.connect(self._target_moved)
        self._controls['wl_line'].sigPositionChanged.connect(self._wl_line_moved)
        self.params['overlay'].changed.connect(self._transform_lines)

        return layout
    
    def set_file(self, filename):
        self._data = ds.load(filename)
        self._data._raw -= self._data.metadata['background']
        self._images[0].setImage(self._data.take_sum('wl').raw)
        self._netname = ds.extract_raw(filename, '(Net[A-Z0-9]*)')[0]
        self._transform_lines()
        self._target_moved(self._controls['target'])
        self._wl_line_moved(self._controls['wl_line'])

    def _target_moved(self, target):
        x, y = target.pos()
        x, y = int(x), int(y)
        self._controls['target_2'].setPos(x + .5, y + .5)
        self._controls['space_line'].setValue(x + .5)
        self._controls['space_line_2'].setValue(y + .5)
        self._images[1].setImage(self._data.take(pos=x).raw)
        self._lines[0].setData(self._data.take(pos=x).take(y=y).raw)

    def _wl_line_moved(self, line):
        wl = int(line.value())
        self._controls['wl_line_2'].setValue(wl)
        self.params['wavelength'].set_value(self._data.wl[wl])
        self._images[2].setImage(self._data.take(wl=wl).raw)


    def _get_coordinates(self):
        self._coordinates = {}
        for network in ("NetW350L075D100", "NetW350L05D150"):
            x, y = np.genfromtxt(
                f"{os.path.dirname(os.path.realpath(__file__))}/{network}_coordinates.csv",
                unpack=True
            )
            matrix = np.genfromtxt(
                f"{os.path.dirname(os.path.realpath(__file__))}/{network}_transform.csv",
            )
            result = np.matmul(matrix, np.vstack((x, y, np.ones(len(x)))))
            result[:2] /= result[2]
            self._coordinates[network] = result[:2]

    def _transform_lines(self):
        if self.params['overlay'].get_value():
            for line in self._net_lines:
                line.setData(self._coordinates[self._netname][1], self._coordinates[self._netname][0])
        else:
            for line in self._net_lines:
                line.setData([0], [0])

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'test.hs'

    app = QtWidgets.QApplication([])
    main = file_viewer.FilesViewer(filename, HSView)
    main.show()
    app.exec()