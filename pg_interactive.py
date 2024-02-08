"""
Set of small tools and shims to make quick plotting with pyqtgraph easier.

MIT License

Copyright (c) 2023 Jakub Dranczewski
Created as part of PhD work supported by the EU ITN EID project CORAL (GA no. 859841).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from pyqtgraph.Qt import QtCore, QtWidgets, QtWidgets
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class Control(QtWidgets.QWidget):
    """
    A slider with some sensible defaults. See get_pg_controls for easy creation.
    """
    def __init__(self, name, values, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.axis_values = values
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QtWidgets.QLabel()
        self.label.setText(name)
        self.layout.addWidget(self.label)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.axis_values)-1)
        self.slider.setTickPosition(self.slider.TickPosition.TicksBelow)
        self.layout.addWidget(self.slider)
        self.valueChanged = self.slider.valueChanged

        self.format = "{:.2f}"
        self.value_label = QtWidgets.QLabel()
        self.value_label.setText(self.format.format(self.axis_values[0]))
        self.layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._update_label)
        self.valueChanged = self.slider.valueChanged

    def _update_label(self, s_value):
        self.value_label.setText(self.format.format(self.axis_values[s_value]))

    def value(self):
        return self.slider.value()


def get_pg(row=1, col=1):
    """
    Produce a row x col grid of PlotItems. Returns the containing GraphicsLayoutWidget
    and a flattened list of the PlotItems.
    """
    w = pg.GraphicsLayoutWidget()
    ax = []
    for i in range(row):
        for j in range(col):
            plot = w.addPlot(row=i, col=j)
            ax.append(plot)
            
    return w, ax


def get_pg_controls(row=1, col=1, **controls):
    """
    Produce a row x col grid of PlotItems with Control sliders below.

    The sliders are defined by providing keyword arguments with lists of values the slider
    should go through. For example::
    
        temps = np.genfromtxt("temps.txt")
        w, w_plot, ax, cdict = get_pg_controls(1, 1, temperatures=temps)
        cdict['temperatures'].valueChanged.connect(update)
    
    will make a slider for the temperature list, and one can connect a function to the slider's
    valueChanged Signal.

    Returns:
        w: the QWidget containing the GraphicsLayoutWidget and the Control sliders
        w_plot: the GraphicsLayoutWidget of the plots
        ax: a flattened list of the PlotItems
        cdict: a dictionary of the Control sliders.
    """
    w_plot, ax = get_pg(row, col)

    w = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout()
    w.setLayout(layout)
    layout.addWidget(w_plot)

    cdict = {}
    for control in controls:
        cw = Control(control, controls[control])
        layout.addWidget(cw)
        cdict[control] = cw
    
    return w, w_plot, ax, cdict


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window, _,  _, _ = get_pg_controls(test=[x for x in range(5)], Test2=[x for x in range(10)])
    window.show()
    app.exec_()