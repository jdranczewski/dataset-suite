from random import sample
import numpy as np
import os
from glob import glob
import scipy.io as scio

from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from matplotlib.pyplot import cm

base = "folder"

# Make the window

app = pg.mkQApp("Fullsensor")

win = QtGui.QMainWindow()
win.setWindowTitle('Fullsensor')
win.resize(1200,600)

cw = QtGui.QWidget()
win.setCentralWidget(cw)
l = QtGui.QGridLayout()
cw.setLayout(l)

imv1 = pg.ImageView()
l.addWidget(imv1, 0, 0, 3, 1)
imv1.view.setAspectLocked(False)
# lr1 = pg.LinearRegionItem(values=[100, 127], orientation='horizontal')
lr1 = pg.InfiniteLine(120, 0, (0,0,255,150), True, hoverPen=(0,0,255,200))
imv1.addItem(lr1)
# lr2 = pg.LinearRegionItem(values=[127, 160], orientation='horizontal', brush=(255, 0, 0, 25))
lr2 = pg.InfiniteLine(150, 0, (255, 0, 0, 150), True, hoverPen=(255, 0, 0, 200))
imv1.addItem(lr2)
iml = QtGui.QLabel()
l.addWidget(iml, 5, 0)


p1 = pg.PlotWidget()
l.addWidget(p1, 0, 1, 1, 1)
plot1 = p1.getPlotItem()

p2 = pg.PlotWidget()
l.addWidget(p2, 1, 1, 1, 1)
plot2 = p2.getPlotItem()

p3 = pg.PlotWidget()
l.addWidget(p3, 2, 1, 1, 1)
plot3 = p3.getPlotItem()

plabel = QtGui.QLabel()
l.addWidget(plabel, 4, 0)
flabel = QtGui.QLabel()
flabel.setAlignment(QtCore.Qt.AlignRight)
l.addWidget(flabel, 4, 1)

dsel = QtGui.QComboBox()
l.addWidget(dsel, 5, 1)

l.setColumnStretch(0,1)
l.setColumnStretch(0,1)

win.show()

# Get and display the data

# Get the folders that contain fullsensor data
samples = [x for x in next(os.walk(base))[1] if len(glob(os.path.join(base, x, "*fullsensor_L*")))]
dsel.addItems(samples)
shots = glob(os.path.join(base, samples[0], "*r_L*_R*.mat")) + glob(os.path.join(base, samples[0], "*r_R*_L*.mat"))[::-1]
# Add a slider for the various powers
ps = QtGui.QSlider(QtCore.Qt.Horizontal)
ps.setMinimum(0)
ps.setMaximum(len(shots)-1)
ps.setTickPosition(ps.TicksBelow)
l.addWidget(ps, 3, 0, 1, 2)

fname = shots[16]
mat = scio.loadmat(fname)
wls = mat.get('calibration')[0]
pixels = mat.get('ypixels')[0].astype(int)
powers = mat.get('PUMPPOWER')[0]
vals = mat.get("DATA").astype(int) - mat.get("BG").astype(int)

imv1.setImage(np.transpose(vals,(0,2,1)))

# Initial setup
colours = cm.viridis((powers-powers[0])/(powers[-1]-powers[0]))*255
i = int(imv1.timeLine.value())
lines = [[], None, [], None, [], None]

# Lineout 1
pixel_0 = int(lr1.value())
for j in range(len(vals)):
    lines[0].append(plot1.plot(wls, vals[j, pixel_0], pen=colours[j]-np.array([0,0,0,150])))
lines[1] = plot1.plot(wls, vals[i, pixel_0], pen='b')

# Integrated
for j in range(len(vals)):
    lines[2].append(plot2.plot(wls, np.mean(vals[j], axis=0), pen=colours[j]-np.array([0,0,0,150])))
lines[3] = plot2.plot(wls, np.mean(vals[i], axis=0), pen=colours[i])

# Lineout 2
pixel_0 = int(lr2.value())
for j in range(len(vals)):
    lines[4].append(plot3.plot(wls, vals[j, pixel_0], pen=colours[j]-np.array([0,0,0,150])))
lines[5] = plot3.plot(wls, vals[i, pixel_0], pen='r')

# The arguments are here for optimisation's sake, they allow us to turn off certain updates when they're not needed
prev_i = 4000
def update(iu=False, blue=True, red=True):
    global prev_i
    i = int(imv1.timeLine.value())

    if iu and prev_i == i:
        return

    if blue:
        pixel_0 = int(lr1.value())
        for j in range(len(vals)):
            lines[0][j].setData(wls, vals[j, pixel_0], pen=colours[j]-np.array([0,0,0,150]))
        lines[1].setData(wls, vals[i, pixel_0], pen='b')

    lines[3].setData(wls, np.mean(vals[i], axis=0), pen=colours[i])

    if red:
        pixel_0 = int(lr2.value())
        for j in range(len(vals)):
            lines[4][j].setData(wls, vals[j, pixel_0], pen=colours[j]-np.array([0,0,0,150]))
        lines[5].setData(wls, vals[i, pixel_0], pen='r')

def change_file():
    global fname, wls, pixels, powers, vals
    fname = shots[ps.value()]
    mat = scio.loadmat(fname)
    wls = mat.get('calibration')[0]
    pixels = mat.get('ypixels')[0].astype(int)
    powers = mat.get('PUMPPOWER')[0]
    vals = mat.get("DATA").astype(int) - mat.get("BG").astype(int)

    plabel.setText(", ".join(fname.split("_")[-2:])[:-4])
    flabel.setText(os.path.basename(fname))

    for j in range(len(vals)):
        lines[2][j].setData(wls, np.mean(vals[j], axis=0), pen=colours[j]-np.array([0,0,0,150]))
    frame = imv1.timeLine.value()
    imv1.setImage(np.transpose(vals,(0,2,1)), autoRange=False)
    imv1.setCurrentIndex(int(frame))
    update()

change_file()

lr1.sigPositionChanged.connect(lambda: update(red=False))
lr2.sigPositionChanged.connect(lambda: update(blue=False))
imv1.timeLine.sigPositionChanged.connect(lambda: update(iu=True))
ps.valueChanged.connect(change_file)

def change_device(name):
    global shots
    shots = glob(os.path.join(base, name, "*r_L*_R*.mat")) + glob(os.path.join(base, name, "*r_R*_L*.mat"))[::-1]
    ps.setMaximum(len(shots)-1)
    # if ps.value() > len(shots)-1:
    #     ps.setValue(len(shots)-1)
    change_file()

dsel.currentTextChanged.connect(change_device)

def mouse_moved(evt):
    pos = evt[0]
    if imv1.getView().sceneBoundingRect().contains(pos):
        mouse_point = imv1.getView().mapSceneToView(pos)
        j, k = int(mouse_point.x()), int(mouse_point.y())
        if 0 <= k < len(vals[0]) and 0 <= j < len(vals[0,0]):
            i = int(imv1.timeLine.value())
            iml.setText("{}, {}, {}".format(wls[j], pixels[k], vals[i,k,j]))
        

# imv1.imageItem.setMouseTracking(True)
proxy = pg.SignalProxy(imv1.imageItem.scene().sigMouseMoved, rateLimit=60, slot=mouse_moved)

if __name__ == '__main__':
    pg.exec()