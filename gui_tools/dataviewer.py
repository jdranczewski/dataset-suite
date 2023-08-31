import datasets1 as ds

import sys

import numpy as np
import skimage.io

from pyqtgraph.Qt import QtWidgets
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class DataViewer(QtWidgets.QWidget):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dataset = ds.load(filename)

        self.layout = QtWidgets.QGridLayout()
        if isinstance(self.dataset, ds.datalist):
            self.layout.addWidget(DatalistLevel(self.dataset))
        elif isinstance(self.dataset, ds.dataset):
            self.layout.addWidget(DatasetLevel(self.dataset))
        self.setLayout(self.layout)


class Level(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QtWidgets.QGridLayout()
        self.child = QtWidgets.QWidget()
        self.layout.addLayout(self.make_layout(), 0, 0)
        self.layout.addWidget(self.child, 1, 0)
        self.setLayout(self.layout)

    def make_layout(self):
        raise NotImplementedError

    def set_child(self):
        new_child = self.make_child()
        self.layout.removeWidget(self.child)
        self.child = new_child
        self.layout.addWidget(self.child, 1, 0)

    def make_child(self):
        return QtWidgets.QWidget()


class DatalistLevel(Level):
    def __init__(self, datalist, *args, **kwargs):
        self.datalist = datalist
        self.name = datalist.axes[0]
        self.offset = 0

        super().__init__(*args, **kwargs)

    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel()
        label.setText(self.name)
        layout.addWidget(label, 0, 0)

        label = QtWidgets.QLabel()
        label.setText(str(getattr(self.datalist, 'metadata', '')))
        label.setWordWrap(True)
        layout.addWidget(label, 1, 0, 1, 2)

        self.dropdown = QtWidgets.QComboBox()

        if isinstance(self.datalist[0], ds.dataset):
            self.dropdown.addItem("--")
            self.dropdown.addItem("--All--")
            self.offset = 2
        
        for item in self.datalist.axis:
            try:
                self.dropdown.addItem("{:.2f}".format(item))
            except ValueError:
                self.dropdown.addItem(str(item))
        layout.addWidget(self.dropdown, 0, 1)
        self.dropdown.currentIndexChanged.connect(self.changed)
        self.changed()
        
        return layout

    def changed(self, index=None):
        self.set_child()

    def make_child(self):
        index = self.dropdown.currentIndex() - self.offset
        if index == -2:
            return QtWidgets.QWidget()
        elif index == -1:
            return MultiPlotLevel(self.datalist)
        else:
            child_ds = self.datalist[index]
            if isinstance(child_ds, ds.datalist):
                return DatalistLevel(child_ds)
            elif isinstance(child_ds, ds.dataset):
                return DatasetLevel(child_ds)


class PlotLevel(Level):
    def __init__(self, dataset, *args, **kwargs):
        self.dataset = dataset

        super().__init__(*args, **kwargs)

    def make_layout(self):
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel()
        label.setText(str(getattr(self.dataset, 'metadata', '')))
        label.setWordWrap(True)
        layout.addWidget(label)

        layout.addWidget(self.make_plot())

        return layout

    def make_plot(self):
        raise NotImplementedError


class MultiPlotLevel(PlotLevel):
    def make_plot(self):
        w = pg.GraphicsLayoutWidget()
        prev_plot = None
        for i, dataset in enumerate(self.dataset):
            plot = w.addPlot(row=0, col=i)

            try:
                plot.setTitle("{:.2f}".format(self.dataset.axis[i]))
            except ValueError:
                plot.setTitle(str(self.dataset.axis[i]))

            if prev_plot is not None:
                plot.setXLink(prev_plot)
                plot.setYLink(prev_plot)

            colours = ds.colours(dataset.power)*255
            for j in range(len(dataset.power)):
                I = dataset.take_raw(power=j)
                plot.plot(dataset.wl, I, pen=colours[j]-np.array([0,0,0,150]))
            prev_plot = plot

        return w


class DatasetLevel(PlotLevel):
    def make_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plt = self.plot_widget.getPlotItem()

        colours = ds.colours(self.dataset.power)*255
        for i in range(len(self.dataset.power)):
            I = self.dataset.take_raw(power=i)
            self.plt.plot(self.dataset.wl, I, pen=colours[i]-np.array([0,0,0,150]))

        return self.plot_widget


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "file"

    app = QtWidgets.QApplication([])

    window = DataViewer(filename)
    window.show()

    app.exec()
