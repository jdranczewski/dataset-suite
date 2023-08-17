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
    def __init__(self, peak_id, dataset, params, name, *args, **kwargs):
        self.peak_id = peak_id
        self.threshold = 0
        super().__init__(dataset, params, name, *args, **kwargs)
        self.showMaximized()

    def make_action_buttons(self, spec=None):
        spec = [['Skip', self.skip], ['Skip all remaining peaks', self.skip_all]]
        return super().make_action_buttons(spec)

    def make_layout(self):
        layout = QtWidgets.QGridLayout()
        lw = pg.GraphicsLayoutWidget()
        layout.addWidget(lw, 0, 0)
        lw2 = pg.GraphicsLayoutWidget()
        layout.addWidget(lw2, 0, 1)
        self.cut_info = QtWidgets.QLabel()
        self.cut_info.setText(str(self.dataset.cut))
        layout.addWidget(self.cut_info, 1, 0)
        self.ase_check = QtWidgets.QCheckBox("ASE")
        layout.addWidget(self.ase_check, 1, 1)
        if self.params['ase'] is not None:
            self.ase_check.setChecked(self.params['ase'])
        self.comment = QtWidgets.QLineEdit()
        layout.addWidget(self.comment, 2, 0, 1, 2)

        self.plots = {
            "main": lw.addPlot(row=0, col=0),
            "sub": lw.addPlot(row=1, col=0),
            "blueshift": lw.addPlot(row=2, col=0),
            "slider": lw.addPlot(row=3, col=0),
            "ll": lw2.addPlot(row=0, col=0),
            "wl": lw2.addPlot(row=1, col=0),
            "lw": lw2.addPlot(row=2, col=0),
        }
        self.plots["sub"].showGrid(y=True)
        self.plots["ll"].showGrid(y=True)
        self.plots["slider"].setMouseEnabled(False, False)
        self.plots["blueshift"].setXRange(0,30)
        lw.ci.layout.setRowStretchFactor(0, 10)
        lw.ci.layout.setRowStretchFactor(1, 5)
        lw2.ci.layout.setRowStretchFactor(0, 2)

        # try:
        self.plot_init()
        # except (ValueError, IndexError):
        #     print("Skipping this one, peak finding problems encountered")
        #     self.close()
        #     raise ReferenceError("This dataset has been processed already")

        return layout

    def plot_init(self):
        colours = ds.colours(self.dataset.power)*255
        for i in range(len(self.dataset.power)):
            I = self.dataset.take_raw(power=i)
            self.plots["main"].plot(self.dataset.wl, I, pen=colours[i]-np.array([0,0,0,150]))

        ranges, init_wl = self.find_ranges()
        self.max_positions = ranges
        self.controls = {
            "init_wl_indicator": pg.InfiniteLine(init_wl, 90, movable=False),
            "power_slider": pg.InfiniteLine(len(self.dataset.power)-1, 90, movable=True, bounds=(0, len(self.dataset.power)-1)),
            "blueshift_slider": pg.InfiniteLine(self.params['fit_range_blueshift'] if self.params['fit_range_blueshift'] else 0, 90, movable=True),
            "power_indicator_ll": pg.InfiniteLine(0, 90, movable=False),
            "power_indicator_wl": pg.InfiniteLine(0, 90, movable=False),
            "power_indicator_lw": pg.InfiniteLine(0, 90, movable=False),
            "fit_range_left": pg.LinearRegionItem(values=ranges[:2], orientation='vertical'),
            "fit_range_right": pg.LinearRegionItem(values=ranges[2:], orientation='vertical', brush=(255, 0, 0, 50)),
            "wl_indicator": pg.InfiniteLine(0, 90, movable=False),
            "threshold_wl_indicator": pg.InfiniteLine(0, 0, movable=False),
            "useful_lw": pg.InfiniteLine(self.dataset.power[self.params['useful_lw']] if self.params['useful_lw'] else 0.075, 90, movable=True)
        }
        if self.params['fit_range_ll_a']:
            self.controls["fit_ll"] = pg.LinearRegionItem(values=(self.dataset.power[self.params['fit_range_ll_a']]-0.001, self.dataset.power[self.params['fit_range_ll_b']]+0.001), orientation='vertical')
        else:
            self.controls["fit_ll"] = pg.LinearRegionItem(values=(self.dataset.power[-4], self.dataset.power[-1]), orientation='vertical')
        self.power_i = 0
        self.controls["power_slider"].sigPositionChanged.connect(self.update_slider)
        self.controls["blueshift_slider"].sigPositionChanged.connect(self.update_blueshift)
        self.controls["blueshift_slider"].sigPositionChangeFinished.connect(self.plot_ll)
        self.controls["fit_range_left"].sigRegionChanged.connect(self.fit_pl)
        self.controls["fit_range_left"].sigRegionChanged.connect(self.plot_ll)
        self.controls["fit_range_right"].sigRegionChanged.connect(self.fit_pl)
        self.controls["fit_range_right"].sigRegionChanged.connect(self.plot_ll)
        self.controls["fit_ll"].sigRegionChanged.connect(self.fit_ll)
        self.plots["main"].addItem(self.controls["init_wl_indicator"])
        self.plots["main"].addItem(self.controls["fit_range_left"])
        self.plots["main"].addItem(self.controls["fit_range_right"])
        self.plots["slider"].addItem(self.controls["power_slider"])
        self.plots["blueshift"].addItem(self.controls["blueshift_slider"])
        self.plots["ll"].addItem(self.controls["power_indicator_ll"])
        self.plots["ll"].addItem(self.controls["fit_ll"])
        self.plots["wl"].addItem(self.controls["power_indicator_wl"])
        self.plots["wl"].addItem(self.controls["threshold_wl_indicator"])
        self.plots["lw"].addItem(self.controls["power_indicator_lw"])
        self.plots["lw"].addItem(self.controls["useful_lw"])
        self.plots["sub"].addItem(self.controls["wl_indicator"])
        self.plots["slider"].setXRange(0, len(self.dataset.power)-1)

        self.lines = {
            "main": {
                "highlight": self.plots["main"].plot(self.dataset.wl, self.dataset.take_raw(power=0), pen=(255,0,0)),
                "pl_fit": self.plots["main"].plot(self.dataset.wl, self.dataset.take_raw(power=0), pen=(0,0,255)),
            },
            "sub": {
                "sub": self.plots["sub"].plot(pen=(255,255,255)),
            },
            "ll": {
                "ll": self.plots["ll"].plot(symbol='x', pen=(255,225,255)),
                "pl": self.plots["ll"].plot(symbol='x', pen=(100,100,100)),
                "fit": self.plots["ll"].plot(pen=(255,0,0)),
            },
            "wl": {
                "wl": self.plots["wl"].plot(symbol='x', pen=(255,225,255)),
            },
            "lw": {
                "lw": self.plots["lw"].plot(symbol='x', pen=(255,225,255)),
            }
        }
        self.update_slider()
        self.plot_ll()
    
    min_range = 7
    max_range = 12
    view_range = 14
    def find_ranges(self):
        # I = self.dataset.take_raw(power=-len(self.dataset.power)//2)
        I = self.dataset.take_raw(power=-1)
        peaks, _ = signal.find_peaks(I, prominence=prominence)
        if not len(peaks):
            raise ReferenceError("No peaks found")
        peak = peaks[self.peak_id]

        if self.params['fit_range_left_a']:
            return ([self.params['fit_range_left_a'], self.params['fit_range_left_b'], self.params['fit_range_right_a'], self.params['fit_range_right_b']],
                    self.dataset.wl[peak])
        else:
            hm = I[peak]/2
            try:
                d = np.array([
                    np.argwhere(I[:peak]<hm)[-1,0]-peak,
                    np.argwhere(I[peak:]<hm)[0,0]
                ])
            except IndexError:
                d = np.array([-1,1])
            view_ranges = np.array([peak+d[0]*self.view_range, peak+d[1]*self.view_range])
            view_ranges[view_ranges >= len(self.dataset.wl)] = len(self.dataset.wl)-1
            view_ranges[view_ranges < 0] = 0
            self.plots["main"].setXRange(self.dataset.wl[view_ranges[0]],
                                        self.dataset.wl[view_ranges[1]])

            fit_ranges = np.array([peak+d[0]*self.max_range,
                                peak+d[0]*self.min_range,
                                peak+d[1]*self.min_range,
                                peak+d[1]*self.max_range])
            fit_ranges[fit_ranges >= len(self.dataset.wl)] = len(self.dataset.wl)-1
            fit_ranges[fit_ranges < 10] = 10 # used to be 226 for some reason
            if fit_ranges[0] == fit_ranges[1]:
                fit_ranges[1] += 10
            if fit_ranges[2] == fit_ranges[3]:
                fit_ranges[2] -= 10
            return self.dataset.wl[fit_ranges], self.dataset.wl[peak]
    
    def update_blueshift(self):
        blueshift = self.controls["blueshift_slider"].value()
        delta_p = self.dataset.power[-1] - self.dataset.power[self.power_i]
        positions = np.copy(self.max_positions)
        positions[1:3] += delta_p*blueshift

        self.controls["fit_range_left"].sigRegionChanged.disconnect(self.plot_ll)
        self.controls["fit_range_right"].sigRegionChanged.disconnect(self.plot_ll)
        self.controls["fit_range_left"].setRegion(positions[:2])
        self.controls["fit_range_right"].setRegion(positions[2:])
        self.controls["fit_range_left"].sigRegionChanged.connect(self.plot_ll)
        self.controls["fit_range_right"].sigRegionChanged.connect(self.plot_ll)

        return blueshift

    def update_slider(self):
        value = self.controls["power_slider"].value()
        if int(value) == self.power_i:
            return
        self.power_i = int(value)
        self.controls["power_indicator_ll"].setValue(self.dataset.power[self.power_i])
        self.controls["power_indicator_lw"].setValue(self.dataset.power[self.power_i])
        self.controls["power_indicator_wl"].setValue(self.dataset.power[self.power_i])
        self.lines["main"]["highlight"].setData(self.dataset.wl, self.dataset.take_raw(power=self.power_i))
        if not self.update_blueshift():
            self.fit_pl()

    def fit_pl(self):
        blueshift = self.controls["blueshift_slider"].value()
        delta_p = self.dataset.power[-1] - self.dataset.power[self.power_i]
        positions = np.concatenate((self.controls["fit_range_left"].getRegion(), self.controls["fit_range_right"].getRegion()))
        self.max_positions = positions
        self.max_positions[1:3] -= delta_p*blueshift

        indices_left, indices_right, indices_full, fit, I = self.fit_pl_raw(self.power_i)
        self.lines["main"]["pl_fit"].setData(self.dataset.wl[indices_full], fit(indices_full))
        self.lines["sub"]["sub"].setData(self.dataset.wl[indices_full], I[indices_full] - fit(indices_full))
        self.plots["sub"].autoRange()
        wl_max_i = np.argmax(I[indices_full] - fit(indices_full))+indices_full[0]
        self.controls["wl_indicator"].setValue(self.dataset.wl[wl_max_i])
        #self.plot_ll()
    
    def plot_ll(self):
        values = []
        wls = []
        lws = []
        for i in range(len(self.dataset.power)):
            indices_left, indices_right, indices_full, fit, I = self.fit_pl_raw(i)
            subtracted = I[indices_full] - fit(indices_full)
            values.append(np.sum(subtracted))
            wl_max_i = np.argmax(subtracted)
            wl_max = self.dataset.wl[wl_max_i+indices_full[0]]
            wls.append(wl_max)
            hm = subtracted[wl_max_i]/2
            try:
                lws.append(self.dataset.wl[np.argwhere(subtracted[wl_max_i:]<hm)[0,0]+indices_full[0]] - self.dataset.wl[np.argwhere(subtracted[:wl_max_i]<hm)[-1,0]-wl_max_i+indices_full[0]])
            except IndexError:
                lws.append(0)
        self.lines["ll"]["ll"].setData(self.dataset.power, values)
        self.lines["ll"]["pl"].setData(self.dataset.power, self.dataset.take_sum('wl').raw-values)
        self.plots["ll"].autoRange()
        self.lines["wl"]["wl"].setData(self.dataset.power, wls)
        self.plots["wl"].autoRange()
        self.lines["lw"]["lw"].setData(self.dataset.power, lws)
        self.plots["lw"].autoRange()
        self.ll_values = np.array(values)
        self.wl_values = np.array(wls)
        self.lw_values = np.array(lws)
        self.fit_ll()
    
    def fit_ll(self):
        indices, fit_c, fit = self.fit_ll_raw()
        x = np.linspace(-fit_c[1]/fit_c[0], self.dataset.power[indices[-1]], 3)
        self.lines["ll"]["fit"].setData(x, fit(x))
        self.threshold = -fit_c[1]/fit_c[0]

        threshold_index = self.power_to_i(self.threshold)
        if threshold_index < len(self.dataset.power):
            self.threshold_wl = np.poly1d(np.polyfit(self.dataset.power[threshold_index:], self.wl_values[threshold_index:], 1))(self.threshold)
            self.controls["threshold_wl_indicator"].setValue(self.threshold_wl)
        self.plots["wl"].autoRange()


    def skip(self):
        self.params['comment'] = self.comment.text()
        self.saveSignal.emit()

    def skip_all(self):
        print("yes")
        self.params['comment'] = self.comment.text()
        self.skipAllSignal.emit()
        # self.saveSignal.emit()

    def save(self):
        self.params['skip'] = 0
        self.params['ase'] = int(self.ase_check.isChecked())
        self.params['comment'] = self.comment.text()

        # Threshold
        indices, fit_c, fit = self.fit_ll_raw()
        self.params['threshold'] = -fit_c[1]/fit_c[0]
        self.params['ll_slope'] = fit_c[0]
        self.params['fit_range_ll_a'], self.params['fit_range_ll_b'] = indices[0], indices[-1]
        self.params['threshold_wl'] = self.threshold_wl

        # Fit ranges
        self.params['fit_range_left_a'], self.params['fit_range_left_b'] = self.max_positions[0], self.max_positions[1]
        self.params['fit_range_right_a'], self.params['fit_range_right_b'] = self.max_positions[2], self.max_positions[3]
        self.params['fit_range_blueshift'] = self.controls["blueshift_slider"].value()

        # Useful linewidths
        self.params['useful_lw'] = self.power_to_i(self.controls['useful_lw'].value())

        # All the plots
        arr = np.vstack((self.dataset.power, self.ll_values, self.wl_values, self.lw_values))
        out = BytesIO()
        np.save(out, arr)
        out.seek(0)
        self.params['arrays'] = out.read()

        return super().save()

    # Convenience functions
    def fit_pl_raw(self, i):
        blueshift = self.controls["blueshift_slider"].value()
        delta_p = self.dataset.power[-1] - self.dataset.power[i]
        positions = np.copy(self.max_positions)
        positions[1:3] += delta_p*blueshift

        I = self.dataset.take_raw(power=i)
        indices_left = np.arange(*self.wl_to_i(positions[:2]))
        indices_right = np.arange(*self.wl_to_i(positions[2:]))
        fit = np.poly1d(np.polyfit(np.concatenate((indices_left, indices_right)),
                               np.concatenate((I[indices_left], I[indices_right])), 3))
        # indices_full = np.arange(self.wl_to_i(self.controls["fit_range_left"].getRegion()[0]),
        #                          self.wl_to_i(self.controls["fit_range_right"].getRegion()[1]))
        indices_full = np.arange(self.wl_to_i(self.max_positions[0]), self.wl_to_i(self.max_positions[-1]))
        return indices_left, indices_right, indices_full, fit, I

    def fit_ll_raw(self):
        indices = np.arange(*self.power_to_i(self.controls["fit_ll"].getRegion()))
        fit_c = np.polyfit(self.dataset.power[indices], self.ll_values[indices], 1)
        fit = np.poly1d(fit_c)
        return indices, fit_c, fit

    def wl_to_i(self, wl):
        m = np.amax(self.dataset.wl)
        try:
            return np.array([np.argwhere(self.dataset.wl>=x)[0,0] if x<m else len(self.dataset.wl) for x in wl])
        except TypeError:
            return np.argwhere(self.dataset.wl>=wl)[0,0] if wl<m else len(self.dataset.wl)

    def power_to_i(self, power):
        #TODO rethink the default of returning len()
        m = np.amax(self.dataset.power)
        try:
            return np.array([np.argwhere(self.dataset.power>=x)[0,0] if x<m else len(self.dataset.power) for x in power])
        except TypeError:
            return np.argwhere(self.dataset.power>=power)[0,0] if power<m else len(self.dataset.power)

class SuperPeakCycler(superhuman.SuperCycler):
    def __init__(self, superwidget, datafile_name, dbconn, param_spec, name, *args, **kwargs):
        datalist = []
        self.initial_data = data = ds.load(datafile_name)
        self.i = 0
        self.j = 0
        self.datafile_name = datafile_name
        # for i, a in enumerate(data):
        #     for j, b in enumerate(a):
        #         for k, c in enumerate(b):
        #             c.add_cut('indices', ",".join((str(i), str(j), str(k))))
        #             datalist.append(c)
        # for i, a in enumerate(data):
        #     for j, b in enumerate(a):
        #         b.add_cut('indices', ",".join((str(i), str(j))))
        #         datalist.append(b)
        for i, b in enumerate(data):
            b.add_cut('indices', ",".join((str(i),)))
            datalist.append(b)
        super().__init__(superwidget, datalist, dbconn, param_spec, name, *args, **kwargs)

    def make_advance(self):
        # print("Advancing")
        dataset = self.datalist[self.i]
        print(self.i)
        peak_id = self.j
        self.progress_bar.setValue(self.i+1)
        
        params = superhuman.SuperParams(self.name, self.param_spec)
        params['datafile'] = self.datafile_name
        params['peak_id'] = peak_id
        params['cut'] = dataset.cut
        params['skip'] = 1

        cursor = self.dbconn.execute(params.command_select('datafile', 'cut', 'peak_id'), (self.datafile_name, str(dataset.cut), peak_id))

        self.j += 1
        # I = dataset.take_raw(power=-len(dataset.power)//2)
        I = dataset.take_raw(power=-1)
        peaks, _ = signal.find_peaks(I, prominence=prominence)
        if self.j == len(peaks) or len(peaks) == 0:
            self.i += 1
            self.j = 0
        
        if cursor.fetchone():
            raise ReferenceError("This dataset has been processed already")
        print(dataset.cut, "Peak:", peak_id, '/', len(peaks))

        return [peak_id], dataset, params

    def get_from_row(self, row):
        indices = ds.extract_raw(row['cut'], "'indices': '([0-9,]+)'")[0]
        data = self.initial_data
        for index in [int(x) for x in indices.split(',')]:
            data = data[index]
        return [row['peak_id']], data

    def skip_all(self):
        print('called')
        dataset = self.sw_instance.dataset
        # I = dataset.take_raw(power=-len(dataset.power)//2)
        I = dataset.take_raw(power=-1)
        peaks, _ = signal.find_peaks(I, prominence=prominence)
        print('skipping all', self.sw_instance.params['peak_id'], len(peaks))
        for peak_id in range(self.sw_instance.params['peak_id'], len(peaks)):
            print(peak_id)
            self.sw_instance.params['peak_id'] = peak_id
            self.dbconn.execute(*self.sw_instance.params.command_insert())
        self.dbconn.commit()
        self.j = len(peaks) - 1
        self.sw_instance.close()

    def next(self):
        super().next()
        # A hack to prevent multiple connections being made
        try:
            self.sw_instance.skipAllSignal.disconnect()
        except (AttributeError, TypeError):
            pass

        try:
            self.sw_instance.skipAllSignal.connect(self.skip_all)
        except AttributeError:
            pass

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    dbconn = sqlite3.connect('ET10s.db')
    dbconn.row_factory = sqlite3.Row

    # window = SuperPeakfinder(data, 0, None, "SuperPeakfinder Test")
    param_spec = {
        'datafile': str,
        'peak_id': int,
        'cut': str,
        'skip': int,
        'ase': int,
        'threshold': float,
        'threshold_wl': float,
        'll_slope': float,
        'fit_range_blueshift': float,
        'fit_range_left_a': float,
        'fit_range_left_b': float,
        'fit_range_right_a': float,
        'fit_range_right_b': float,
        'fit_range_ll_a': int,
        'fit_range_ll_b': int,
        'useful_lw': int,
        'arrays': sqlite3.Binary,
        'comment': str
    }
    window = SuperPeakCycler(SuperPeakfinder, r"file", dbconn, param_spec, "ET10s")
    window.show()

    app.exec_()

    dbconn.close()
