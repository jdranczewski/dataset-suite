import superhuman
import datasets1 as ds

import numpy as np
from scipy import signal
import sqlite3
from io import BytesIO

from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg

prominence = 500

class SuperPeakfinder(superhuman.SuperWidget):
    skipAllSignal = QtCore.Signal()
    def __init__(self, dataset, params, name, *args, **kwargs):
        super().__init__(dataset, params, name, *args, **kwargs)
        # self.showMaximized()

    def make_action_buttons(self, spec=None):
        spec = [['Skip', self.skip]]
        return super().make_action_buttons(spec)

    def make_layout(self):
        layout = QtWidgets.QGridLayout()
        lw = pg.GraphicsLayoutWidget()
        layout.addWidget(lw, 0, 0, 1, 2)
        self.cut_info = QtWidgets.QLabel()
        self.cut_info.setText(str(self.dataset.cut))
        layout.addWidget(self.cut_info, 1, 0)
        self.threshold_info = QtWidgets.QLabel()
        self.threshold_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.threshold_info, 1, 1)
        self.comment = QtWidgets.QLineEdit()
        if self.params['comment'] is not None:
            self.comment.setText(self.params['comment'])
        layout.addWidget(self.comment, 2, 0, 1, 2)

        self.plots = {
            "main": lw.addPlot(row=0, col=0),
        }
        self.plots["main"].showGrid(y=True)

        # try:
        self.plot_init()
        # except (ValueError, IndexError):
        #     print("Skipping this one, peak finding problems encountered")
        #     self.close()
        #     raise ReferenceError("This dataset has been processed already")

        return layout

    def plot_init(self):
        self.controls = {}

        arrays = np.load(BytesIO(self.params["arrays"]))
        self.powers = arrays[1]
        self.ll_values = arrays[2]

        if self.params['fit_indices']:
            a, b = [int(x) for x in self.params['fit_indices'].split(':')]
            if b > len(self.powers):
                b = len(self.powers)
            self.controls["fit_ll"] = pg.LinearRegionItem(values=(self.powers[a]-0.001, self.powers[b-1] + 0.001), orientation='vertical')
        else:
            self.controls["fit_ll"] = pg.LinearRegionItem(values=(self.powers[-4], self.powers[-1]), orientation='vertical')
        self.controls["fit_ll"].sigRegionChanged.connect(self.fit_ll)
        self.plots["main"].addItem(self.controls["fit_ll"])

        self.lines = {
            "main": {
                "ll": self.plots["main"].plot(symbol='x', pen=(255,225,255)),
                "fit": self.plots["main"].plot(pen=(255,0,0)),
            }
        }
        self.lines["main"]["ll"].setData(self.powers, self.ll_values)
        self.fit_ll()

    def skip(self):
        self.params['skip'] = 1
        self.params['changed'] = 1
        self.params['comment'] = self.comment.text()
        self.saveSignal.emit()

    def save(self):
        self.params['skip'] = 0
        self.params['changed'] = 1
        self.params['comment'] = self.comment.text()

        # Threshold
        indices, fit_c, fit, p = self.fit_ll_raw_full()
        self.params['threshold'] = -fit_c[1]/fit_c[0]
        self.params['ll_slope'] = fit_c[0]
        self.params['threshold_error'] = (np.sqrt(p[0,0])/abs(fit_c[0]) + np.sqrt(p[1,1])/abs(fit_c[1])) * -(fit_c[1]/fit_c[0])
        self.params['fit_indices'] = f"{indices[0]}:{indices[-1]+1}"

        return super().save()
    
    def fit_ll(self):
        indices, fit_c, fit = self.fit_ll_raw()
        x = np.linspace(-fit_c[1]/fit_c[0], self.powers[indices[-1]], 3)
        self.lines["main"]["fit"].setData(x, fit(x))
        self.threshold = -fit_c[1]/fit_c[0]
        self.threshold_info.setText(f"{self.threshold:.5f}")

    # Convenience functions
    def fit_ll_raw(self):
        indices = np.arange(*self.power_to_i(self.controls["fit_ll"].getRegion()))
        fit_c = np.polyfit(self.powers[indices], self.ll_values[indices], 1)
        fit = np.poly1d(fit_c)
        return indices, fit_c, fit
    
    def fit_ll_raw_full(self):
        indices = np.arange(*self.power_to_i(self.controls["fit_ll"].getRegion()))
        fit_c, p = np.polyfit(self.powers[indices], self.ll_values[indices], 1, cov=True)
        fit = np.poly1d(fit_c)
        return indices, fit_c, fit, p

    def power_to_i(self, power):
        #TODO rethink the default of returning len()
        m = np.amax(self.powers)
        try:
            return np.array([np.argwhere(self.powers>=x)[0,0] if x<m else len(self.powers) for x in power])
        except TypeError:
            return np.argwhere(self.powers>=power)[0,0] if power<m else len(self.powers)


class SuperPeakCycler(superhuman.SuperCycler):
    def __init__(self, superwidget, dbconn, param_spec, name, *args, **kwargs):
        datalist = []
        super().__init__(superwidget, datalist, dbconn, param_spec, name, *args, **kwargs)

    def get_from_row(self, row):
        data = ds.load(row['datafile'])
        for index in [int(x) for x in row['indices'].split(', ')]:
            data = data[index]
        return [], data


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    dbconn = sqlite3.connect(r"file")
    dbconn.row_factory = sqlite3.Row

    # window = SuperPeakfinder(data, 0, None, "SuperPeakfinder Test")
    param_spec = {
        'datafile': str,
        'indices': str,
        'peak_location': int,
        'cut': str,
        'skip': int,
        'ase': int,
        'fit_indices': str,
        'threshold': float,
        'threshold_error': float,
        'threshold_wl': float,
        'll_slope': float,
        'arrays': sqlite3.Binary,
        'comment': str,
        'changed': int
    }
    window = SuperPeakCycler(SuperPeakfinder, dbconn, param_spec, "ET10s_new")
    window.show()

    app.exec()

    dbconn.close()
