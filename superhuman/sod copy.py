import pyperclip
import spe_loader as sl
import os
import numpy as np
from scipy import signal

import datasets1 as ds
import super_peakfinder

from pyqtgraph.Qt import QtCore, QtGui

import matplotlib.pyplot as plt

class TableRow:
    def __init__(self, prefix):
        self.prefix = prefix
        self.labelw = QtGui.QLabel()
        self.labelw.setText(prefix[:30] + '...')
        self.buttonw = QtGui.QPushButton("Show")
        # self.buttonw.clicked.connect(lambda: show(self.prefix))
        def lol():
            test = TableRow("prefix")
            test.insert(table_layout, 1)
        self.buttonw.clicked.connect(lol)
    
    def insert(self, layout, row):
        layout.addWidget(self.labelw, row, 0)
        layout.addWidget(self.buttonw, row, 1)

ref = []

def show(prefix = None):
    if not prefix:
        prefix = pyperclip.paste()
    print(prefix)

    base = "folder"
    files = ds.glob(os.path.join(base, prefix+"_I_*"), no=('raw',))
    ds.sort_by(files, "_P_")

    # Read the files into a dataset (in contrast to a datalist, we know the dimensions will be ok here)
    ds_scan = None
    # progress_bar.setMaximum(len(files))
    for i, file in enumerate(files): # Power files in a run
        # print(file)
        # Get the laser power and integration time using their regex signatures
        P, I = ds.extract(file, "_P_", "_I_")
        # Get the data out of the file
        # wls, counts = np.genfromtxt(file, delimiter=",", unpack=True, skip_header=1)
        spe_files = sl.load_from_files([file])
        wls = spe_files.wavelength
        counts = np.squeeze(spe_files.data)
        # Normalise integration time to 100ms
        counts /= I/100
        # Make a dataset and join it with the full power scan one. Need to add a 'power' axis for that, dim 1
        ds_single = ds.dataset(counts, wl=wls).expand('power', P/1000)
        if ds_scan:
            ds_scan = ds_scan.join(ds_single, "power")
        else:
            ds_scan = ds_single
        # progress_bar.setValue(i+1)
    print(ds_scan)
    return ds_scan
    spw = super_peakfinder.SuperPeakfinder(0, ds_scan, {}, prefix)
    spw.show()
    ref.append(spw)

prefix = "prefix"
dataset = show(prefix)

fig, ax = plt.subplots()
# for i in range(len(dataset.power)):
ax.plot(dataset.wl, dataset.take_raw(power=-1))
peaks, _ = signal.find_peaks(dataset.take_raw(power=-1), prominence=1000)
ax.plot(dataset.wl[peaks], dataset.take_raw(power=-1)[peaks], 'x')

plt.show()

# app = QtGui.QApplication([])

# main = QtGui.QWidget()
# main.setWindowTitle("SuperHuman on Demand")
# main_layout = QtGui.QVBoxLayout()
# main.setLayout(main_layout)

# b = QtGui.QPushButton("Open from clipboard")
# b.clicked.connect(show)
# main_layout.addWidget(b)

# table_layout = QtGui.QGridLayout()
# main_layout.addLayout(table_layout)

# progress_bar = QtGui.QProgressBar()
# main_layout.addWidget(progress_bar)

# # For testing
# test = TableRow("prefix")
# test.insert(table_layout, 0)
# main_layout.addWidget(QtGui.QLabel("The 'open from clipboard' option still works if you have the prefix copied,\nI'm just experimenting with other file read options."))

# main.show()

# app.exec_()