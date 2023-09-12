from pyqtgraph.Qt import QtCore, QtWidgets, QtWidgets
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class Control(QtWidgets.QWidget):
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
    w = pg.GraphicsLayoutWidget()
    ax = []
    for i in range(row):
        for j in range(col):
            plot = w.addPlot(row=i, col=j)
            ax.append(plot)
            
    return w, ax


def get_pg_controls(row=1, col=1, **controls):
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