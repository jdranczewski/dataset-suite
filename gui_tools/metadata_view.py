import file_viewer
import puzzlepiece as pzp
from qtpy import QtWidgets, QtCore

import pyqtgraph as pg
import datasets as ds
import numpy as np
from scipy import signal

from tqdm import tqdm

import sys, os

class MetaView(file_viewer.FileView):
    def custom_layout(self):
        """
        I would like to display:
            As a time series:
                'full_power',
                'full_power_final'
                'stage_pos',
                'time_taken'
            As some sort of scatter?
                'powers' (in some way as a function of label I guess)
            As plots that evolve:
                'background'
                'full_power_spectrum'
                'reference_spectra'
        """
        layout = QtWidgets.QGridLayout()

        self.gl = pg.GraphicsLayoutWidget()
        layout.addWidget(self.gl, 0, 0)
        self.plots = {}
        self.lines = {}

        self.plots['power_in'] = self.gl.addPlot(0, 0)
        self.lines['full_power'] = self.plots['power_in'].plot([], [])
        self.lines['full_power_final'] = self.plots['power_in'].plot([], [], pen=(0, 255, 255, 255))

        self.plots['stage_pos'] = self.gl.addPlot(0, 1)
        self.lines['stage_pos'] = self.plots['stage_pos'].plot([], [])

        self.plots['time_taken'] = self.gl.addPlot(0, 2)
        self.lines['time_taken'] = self.plots['time_taken'].plot([], [])

        return layout
    
    def set_file(self, filename):
        files = ds.glob(filename + '*_meta.ds')
        tracked_vals = {
            'full_power': [],
            'full_power_final': [],
            'stage_pos': [],
            'time_taken': []
        }

        for file in tqdm(files):
            data = ds.load(file)
            for key in tracked_vals.keys():
                tracked_vals[key].append(data[key])
        
        for key in tracked_vals.keys():
            self.lines[key].setData(tracked_vals[key])



class MetaView2(file_viewer.FileView):
    def define_params(self):
        pzp.param.progress(self, 'loading')(None)

    def custom_layout(self):
        """
        I would like to display:
            As a time series:
                'full_power', ✓
                'full_power_final' ✓
                'stage_pos', ✓
                'time_taken'
            As some sort of scatter?
                'powers' (in some way as a function of label I guess) ✓
            As plots that evolve:
                'background' ✓
                'full_power_spectrum' ✓
                'reference_spectra' ✓
        Other things to include:
            infinite lines ✓
            progress bar ✓
            remove labels ✓
            mat file support 
        """
        layout = QtWidgets.QGridLayout()

        self.gl = pg.GraphicsLayoutWidget()
        layout.addWidget(self.gl, 0, 0)

        self.plots = []
        self.images = []
        self.in_lines = []
        self.in_ref = []
        self.out_lines = []
        self.inf_lines = []

        for i in range(12):
            col = i % 6
            row = (i // 6) * 3

            self.plots.append(new_plots := [
                self.gl.addPlot(row, col),
                self.gl.addPlot(row+1, col),
                self.gl.addPlot(row+2, col)
            ])

            self.images.append(ia := pg.ImageItem(border='w', axisOrder='row-major'))
            new_plots[0].addItem(ia)

            self.in_lines.append(il := pg.ScatterPlotItem(size=2))
            new_plots[1].addItem(il)
            self.in_ref.append(new_plots[1].plot([], [], pen=(255, 0, 0, 255)))
            if i == 10:
                self.in_ref.append(new_plots[1].plot([], [], pen=(255, 0, 255, 255)))

            self.out_lines.append(new_plots[2].plot([], []))

            for j in range(1, 3):
                self.inf_lines.append(il := pg.InfiniteLine(0))
                new_plots[j].addItem(il)
                if col and not i==11:
                    new_plots[j].getAxis('left').setStyle(showValues=False)

        for i in range(1, 12):
            self.plots[i][0].setXLink(self.plots[0][0])
            self.plots[i][0].setYLink(self.plots[0][0])
        for i in range(1, 11):
            self.plots[i][1].setXLink(self.plots[0][1])
            self.plots[i][2].setXLink(self.plots[0][2])
            self.plots[i][1].setYLink(self.plots[0][1])
            self.plots[i][2].setYLink(self.plots[0][2])

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1)
        self.slider.setTickPosition(self.slider.TickPosition.TicksBelow)
        layout.addWidget(self.slider, 1, 0)
        self.slider.valueChanged.connect(self._update_i)

        return layout
    
    def set_file(self, filename):
        files = ds.glob(filename + '[0-9][0-9][0-9][0-9]_meta.*')
        spectra = []
        full = []
        bg = []
        labels = []
        powers = []
        ref_powers = []
        fp = []
        fpf = []
        stage_pos = []

        for i, file in enumerate(self.params['loading'].iter(tqdm(files))):
            if 'ds' in file:
                data = ds.load(file)
            else:
                from scipy.io import loadmat
                data = loadmat(file)
                for key in data.keys():
                    data[key] = np.squeeze(data[key])
            spectra.append(data['reference_spectra'])
            full.append(data['full_power_spectrum'])
            bg.append(data['background'])
            powers.append(data['powers'])
            labels.append(data['labels'])
            ref_powers.append(data['reference_powers'])
            fp.append(data['full_power'])
            fpf.append(data['full_power_final'])
            stage_pos.append(data['stage_pos'])
        self.refs = np.array(spectra)
        self.refs = np.append(self.refs, np.asarray(full)[:, None, :, :], 1)
        self.refs = np.append(self.refs, np.asarray(bg)[:, None, :, :], 1)

        powers = np.concatenate(powers)
        labels = np.concatenate(labels)
        ref_powers = np.asarray(ref_powers)
        ref_powers = np.append(ref_powers, np.asarray(fp)[:, None], 1)
        ref_powers = np.append(ref_powers, np.asarray(fpf)[:, None], 1)
        x = np.arange(len(powers))
        for i in range(12):
            mask = labels == i
            # print(labels, mask)
            self.in_lines[i].setData(x[mask], powers[mask])
            double_up = lambda arr: [arr[i//2] for i in range(len(arr)*2)]
            self.in_ref[i].setData(
                double_up(np.arange(len(ref_powers)+1)*1000)[1:-1],
                double_up(ref_powers[:, i])
            )
        self.in_ref[12].setData(stage_pos)

        for i in range(12):
            self.out_lines[i].setData(np.sum(np.sum(self.refs[:, i], 1), 1))
        all_out = np.sum(np.sum(self.refs, 2), 2)[:, :-1]
        self.plots[0][2].setYRange(np.amin(all_out), np.amax(all_out))
        self.plots[0][1].setYRange(
            np.amin([np.amin(powers), np.amin(ref_powers)]),
            np.amax([np.amax(powers), np.amax(ref_powers)])
        )

        self.slider.setMaximum(len(files)-1)
        self._update_i(0)

    def _update_i(self, i):
        _max = np.amax(self.refs[:, 10])
        _min = np.mean(self.refs[:, 11])
        for j in range(11):
            self.images[j].setImage(self.refs[i, j], levels=(_min, _max))
        _max = np.amax(self.refs[:, 11])
        self.images[11].setImage(self.refs[i, 11], levels=(_min, _max))
        for j, line in enumerate(self.inf_lines):
            if not j%2 and j<21:
                line.setValue((i+.5)*1000)
            else:
                line.setValue(i)



class FilesViewer(file_viewer.FilesViewer):
    def __init__(self, filename, viewer=MetaView2, *args, **kwargs):
        if '.ds' in filename:
            filename = filename[:-12]
        if '.mat' in filename:
            filename = filename[:-13]
        super().__init__(filename, viewer, *args, **kwargs)

    def _list_files(self, filename):
        folder = os.path.dirname(filename)

        files = ds.glob(folder+'/*_meta.*')
        prefixes = list(set([x[:-10 - len(x.split('.')[1])] for x in files]))
        prefixes.sort()

        crop = len(folder)+1
        for name in prefixes:
            yield folder, name[crop:]


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'test.hs'

    app = QtWidgets.QApplication([])
    main = FilesViewer(filename, MetaView2)
    main.show()
    app.exec()