import file_viewer
import puzzlepiece as pzp
from qtpy import QtWidgets, QtCore

import pyqtgraph as pg
import datasets as ds
import numpy as np
import sys

from skimage.transform import ProjectiveTransform
from scipy.signal import find_peaks

class ModeView(file_viewer.FileView):
    def __init__(self, *args, **kwargs):
        self._get_transformation()
        super().__init__(*args, **kwargs)

    def _get_transformation(self):
        network = "NetW350L05D150"
        self._net_x, self._net_y = np.genfromtxt(
            f"C:/Users/jbd17/OneDrive - Imperial College London/PhD/Data/ML/20240126_Toriel120_lls_tests_scans/{network}_coordinates.csv",
            unpack=True
        )
        matrix = np.genfromtxt(
            f"C:/Users/jbd17/OneDrive - Imperial College London/PhD/Data/ML/20240126_Toriel120_lls_tests_scans/{network}_transform.csv",
        )
        self._tform3 = ProjectiveTransform(matrix=matrix)

    def set_file(self, filename):
        data = ds.load(filename)
        for key in data.keys():
            setattr(self, "_"+key, data[key])
        self._scatters[0].setData(x=np.asarray(self._peak_wl), y=np.asarray(self._peak_i), width=np.asarray(self._peak_w))
        self._scatters[5].setData(self._peak_wl, self._peak_i)
        self._scatters[1].setData(self._peak_wl, self._peak_i)
        self._lines[0].setData(np.amax(self._spectra, 0))
        self._region_changed()

    def custom_layout(self):
        layout = QtWidgets.QGridLayout()

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        w = pg.GraphicsLayoutWidget()
        layout.addWidget(w, 0, 0)
        ax = [w.addPlot(i%2, i//2) for i in range(4)]

        ax[0].addItem(ebs := pg.ErrorBarItem())
        # Maybe another layer? Feels silly but will probably be faster
        ax[0].addItem(bg_scatter := pg.ScatterPlotItem(brush=(100, 100, 150, 255)))
        ax[0].addItem(roi_peaks := pg.ScatterPlotItem(pen=None, brush=(255, 255, 255, 150)))
        ax[0].addItem(sc_peaks := pg.ScatterPlotItem(brush=(255, 100, 100, 255)))
        ax[0].addItem(scatter := pg.ScatterPlotItem(pen=None, brush=None))
        ax[0].addItem(lr := pg.LinearRegionItem((450, 500), 'vertical'))

        ax[1].addItem(lr2 := pg.LinearRegionItem((0, 50), 'vertical', movable=False))
        max_plot = ax[1].plot(pen=(13, 71, 161, 50))
        line_highlighted = ax[1].plot(pen=(245, 124, 0, 255))
        line_all = ax[1].plot(pen=(150, 150, 150, 50))
        ax[1].addItem(l_peaks := pg.ScatterPlotItem())
        ax[1].addItem(target := pg.TargetItem(movable=False))
        ax[1].setXLink(ax[0])
        ax[1].setYLink(ax[0])

        ax[2].addItem(image := pg.ImageItem())
        self._image = image
        r=2
        ax[2].addItem(circle := pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r*2, r*2))  # x, y, width, height
        circle.setPen(pg.mkPen((255, 255, 0, 150)))
        result = self._tform3._apply_mat(np.vstack((self._net_x, self._net_y)).T, self._tform3.params).T
        ax[2].plot(result[1], result[0], pen=(255, 255, 255, 80))

        roi_item = pg.ROI([0, 0], [3, 7], pen=(255, 255, 0, 200))
        ax[2].addItem(roi_item)

        line_roi = ax[3].plot(pen=(150, 150, 150, 50))
        line_roi_selected = ax[3].plot(pen=(13, 71, 161, 150))
        line_roi_main = ax[3].plot(pen=pg.mkPen(color=(245, 124, 0, 255), dash=[5, 5]))
        ax[3].addItem(lr3 := pg.LinearRegionItem((0, 50), 'vertical', movable=False))
        ax[3].setXLink(ax[0])
        ax[3].setYLink(ax[0])

        self._scatters = [ebs, scatter, sc_peaks, l_peaks, roi_peaks, bg_scatter]
        self._lines = [max_plot, line_highlighted, line_all, line_roi, line_roi_selected, line_roi_main]
        self._controls = [lr, lr2, target, circle, roi_item, lr3]
        scatter.sigClicked.connect(self._point_clicked)
        lr.sigRegionChanged.connect(self._region_changed)
        roi_item.sigRegionChanged.connect(self._roi_changed)

        return layout
    
    def _point_clicked(self, scatter, points, event):
        self._i_clicked = i = points[0].index()
        counts = self._spectra[self._spectra_i[i]]
        self._lines[1].setData(np.arange(len(self._spectra[0])), counts)
        self._controls[2].setPos(self._peak_wl[i], self._peak_i[i])
        r=2
        self._controls[3].setRect(self._peak_p[i][1]+.5-r,
                    self._peak_p[i][0]+.5-r,
                    r*2, r*2)
        self._controls[4].setPos(self._peak_p[i][1]-1, self._peak_p[i][0]-3)
        peaks, _ = find_peaks(counts, prominence=10, distance=10)
        self._scatters[2].setData(peaks, counts[peaks])
        self._scatters[3].setData(peaks, counts[peaks])
        self._roi_changed()
    
    def _region_changed(self):
        min, max = self._controls[0].getRegion()
        self._controls[1].setRegion((min, max))
        self._controls[5].setRegion((min, max))
        values = np.zeros((126, 256))
        self._mask = mask = (self._peak_wl >= min) & (self._peak_wl <= max)
        values[self._peak_p[:, 1][mask], self._peak_p[:, 0][mask]] += self._peak_i[mask]
        
        if np.sum(mask):
            x = (np.concatenate([
                np.vstack([np.arange(len(self._spectra[0]))[::8]]*len(self._spectra_i[mask])),
                np.full((len(self._spectra_i[mask]), 1), np.nan)],
            axis=1)).flatten()
            y = (np.concatenate([self._spectra[self._spectra_i[mask]][:, ::8], np.full((len(self._spectra_i[mask]), 1), np.nan)], axis=1)).flatten()
        else:
            x, y = [], []
        self._lines[2].setData(x, y)
        self._image.setImage(values)
        self._roi_changed()

    def _roi_changed(self):
        # Make a mask
        # Highlight the points in plot 0
        # Plot relevant spectra in plot 3
        # Highlight spectra chosen by the region
        roi = self._controls[4]
        a, b, c, d = roi.pos()[0]-1, roi.pos()[0]-1 + roi.size()[0], roi.pos()[1], roi.pos()[1] + roi.size()[1]
        mask_x = (a < self._peak_p[:, 1]) & (b > self._peak_p[:, 1])
        mask_y = (c < self._peak_p[:, 0]) & (d > self._peak_p[:, 0])
        mask_roi = mask_x & mask_y

        if np.sum(mask_roi):
            x = (np.concatenate([
                np.vstack([np.arange(len(self._spectra[0]))[::8]]*len(self._spectra_i[mask_roi])),
                np.full((len(self._spectra_i[mask_roi]), 1), np.nan)],
            axis=1)).flatten()
            y = (np.concatenate([self._spectra[self._spectra_i[mask_roi]][:, ::8], np.full((len(self._spectra_i[mask_roi]), 1), np.nan)], axis=1)).flatten()
        else:
            x, y = [], []
        self._lines[3].setData(x, y)
        self._scatters[4].setData(self._peak_wl[mask_roi], self._peak_i[mask_roi])

        mask_selected = self._mask & mask_roi
        if np.sum(mask_selected):
            x = (np.concatenate([
                np.vstack([np.arange(len(self._spectra[0]))[::8]]*len(self._spectra_i[mask_selected])),
                np.full((len(self._spectra_i[mask_selected]), 1), np.nan)],
            axis=1)).flatten()
            y = (np.concatenate([self._spectra[self._spectra_i[mask_selected]][:, ::8], np.full((len(self._spectra_i[mask_selected]), 1), np.nan)], axis=1)).flatten()
        else:
            x, y = [], []
        self._lines[4].setData(x, y)

        if hasattr(self, "_i_clicked") and mask_roi[self._i_clicked]:
            self._lines[5].setData(self._spectra[self._spectra_i[self._i_clicked]])
        else:
            self._lines[5].setData([], [])

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = 'test.hs'

    app = pzp.QApp([])
    main = file_viewer.FilesViewer(filename, ModeView)
    main.show()
    app.exec()