print("Importing...")
import sys
import os
import math

import skimage.io

from pyqtgraph.Qt import QtWidgets, QtGui
import pyqtgraph as pg

from tqdm import tqdm
import pyperclip


class ValueDisplay:
    """
    Provides a pair of widgets to display a value easily
    """
    def __init__(self, name, _format="{:.1f}"):
        self.name = name
        self.format = _format

        self.name_label = QtWidgets.QLabel()
        self.name_label.setText(self.name)

        self.value_label = QtWidgets.QLabel()
        self.name_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.value_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        self.set_value(0)
    
    def set_value(self, value):
        self.value_label.setText(self.format.format(value))


class SEMHelper(QtWidgets.QWidget):
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.showMaximized()

        self.filename = filename
        self.setLayout(self.make_layout())

        self.pixelsize = 0
        self.set_image(filename)

    def set_image(self, filename):
        self.setWindowTitle(filename)
        self.filename = filename

        # Open the image
        image = skimage.io.imread(filename).T
        self.pixelsize = None
        # Get metadata (needs to be from a Hitachi microscope I think)
        try:
            with open(filename.split('.')[0]+'.txt', 'r') as f:
                for line in f:
                    if 'PixelSize' in line:
                        self.pixelsize = float(line.split("=")[1])
                    if 'StagePositionT' in line:
                        self.angle_input.setValue(float(line.split("=")[1]))
            if not self.pixelsize:
                raise ValueError("No metadata for the image resolution")
        except FileNotFoundError:
            self.pixelsize = 1

        self.image_view.setImage(image)
        self.targets_updated()


    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        self.image_view = pg.ImageView()
        layout.addWidget(self.image_view, 0, 0)

        self.controls = {
            "target_top": pg.TargetItem((150,250), pen=(255,0,0)),
            "line_top": pg.InfiniteLine(250, 0, pen=(255,0,0,100)),
            "line_left": pg.InfiniteLine(150, 90, pen=(255,0,0,100)),
            "target_bottom": pg.TargetItem((250,150), pen=(0,0,255)),
            "line_bottom": pg.InfiniteLine(150, 0, pen=(0,0,255,100)),
            "line_right": pg.InfiniteLine(250, 90, pen=(0,0,255,100)),
            "side": pg.PlotDataItem((150,250), (250,150), pen=(50,50,50))
        }
        for key in self.controls:
            self.image_view.addItem(self.controls[key])
        self.controls["target_top"].sigPositionChanged.connect(self.targets_updated)
        self.controls["target_bottom"].sigPositionChanged.connect(self.targets_updated)

        layout.addLayout(self.make_control_column(), 0, 1)

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)

        return layout

    def make_control_column(self):
        layout = QtWidgets.QVBoxLayout()
        separator = QtWidgets.QFrame()
        separator.setFrameShape(separator.Shape.HLine)
        separator.setFrameShadow(separator.Shadow.Sunken)

        ### Values display
        values_layout = QtWidgets.QGridLayout()

        self.values = {
            "width": ValueDisplay("Width", "{:.1f}nm"),
            "height": ValueDisplay("Height", "{:.1f}nm"),
            "distance": ValueDisplay("Distance", "{:.1f}nm"),
            "angle": ValueDisplay("Angle", "{:.1f}°"),
        }

        for i, key in enumerate(self.values):
            values_layout.addWidget(self.values[key].name_label, i, 0)
            values_layout.addWidget(self.values[key].value_label, i, 1)

        def copy():
            xt, yt = self.controls["target_top"].pos()
            xb, yb = self.controls["target_bottom"].pos()

            width = abs(-(xt-xb) * self.pixelsize)
            height = abs((yt-yb) * self.pixelsize)
            text = "{:.2f}\t{:.2f}".format(width, height)
            pyperclip.copy(text)

        button = QtWidgets.QPushButton("Copy")
        button.clicked.connect(copy)
        layout.addWidget(button)

        layout.addLayout(values_layout)
        layout.addWidget(separator)

        ### Angle correction
        angle_layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel()
        label.setText("Angle (deg)")
        angle_layout.addWidget(label, 0, 0)

        self.angle_input = QtWidgets.QDoubleSpinBox()
        self.angle_input.setMaximum(100000)
        self.angle_input.valueChanged.connect(self.targets_updated)
        angle_layout.addWidget(self.angle_input, 0, 1)

        self.values["height_corrected"] = ValueDisplay("Height corrected", "{:.1f}nm")
        self.values["distance_corrected"] = ValueDisplay("Distance corrected", "{:.1f}nm")
        self.values["total_d_corrected"] = ValueDisplay("Total d. corrected", "{:.1f}nm")

        for i, key in enumerate(("height_corrected", "distance_corrected", "total_d_corrected")):
            angle_layout.addWidget(self.values[key].name_label, i+1, 0)
            angle_layout.addWidget(self.values[key].value_label, i+1, 1)

        layout.addLayout(angle_layout)

        ## Folder view
        layout.addWidget(self.make_folder_view())

        layout.addWidget(separator)
        self.check_invert = QtWidgets.QCheckBox("Invert y")
        self.check_invert.clicked.connect(self.invert_clicked)
        layout.addWidget(self.check_invert)

        # layout.addStretch()

        return layout

    def make_folder_view(self):
        container = QtWidgets.QScrollArea()
        main = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        folder = os.path.dirname(self.filename)
        for file in tqdm(os.listdir(folder)):
            if '.jpg' in file or '.tif' in file:
                button = ImageButton(folder, file)
                layout.addWidget(button)
                if button.path == self.filename:
                    button.click()
                button.clicked.connect(self.folder_button_clicked)

        main.setLayout(layout)
        container.setWidget(main)
        return container
    
    def folder_button_clicked(self):
        self.set_image(self.sender().path)

    def invert_clicked(self, checked):
        self.image_view.getView().invertY(not checked)


    def targets_updated(self):
        xt, yt = self.controls["target_top"].pos()
        xb, yb = self.controls["target_bottom"].pos()
        
        self.controls["line_top"].setValue(yt)
        self.controls["line_bottom"].setValue(yb)
        self.controls["line_left"].setValue(xt)
        self.controls["line_right"].setValue(xb)
        self.controls["side"].setData((xb, xt), (yb, yt))

        self.values['width'].set_value(-(xt-xb) * self.pixelsize)
        self.values['height'].set_value((yt-yb) * self.pixelsize)
        self.values['distance'].set_value(math.sqrt((yt-yb)**2 + (xt-xb)**2) * self.pixelsize)
        self.values['angle'].set_value(math.atan2(xb-xt, yt-yb)*180/math.pi)
        
        angle = self.angle_input.value() / 180 * math.pi
        if angle:
            self.values['height_corrected'].set_value((yt-yb) * self.pixelsize / math.sin(angle))
        else:
            self.values['height_corrected'].set_value(0)
        dy = (yt-yb) / math.cos(angle)
        self.values['distance_corrected'].set_value(dy * self.pixelsize)
        self.values['total_d_corrected'].set_value(math.sqrt((dy)**2 + (xt-xb)**2) * self.pixelsize)


class ImageButton(QtWidgets.QRadioButton):
    def __init__(self, folder, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path = os.path.join(folder, filename)
        self.filename = os.path.basename(filename)

        self.setText(self.filename)
        icon = pg.QtGui.QIcon(pg.QtGui.QPixmap(self.path))
        self.setIcon(icon)
        self.setIconSize(pg.QtCore.QSize(244, 183))

    def make_layout(self):
        layout = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel()
        self.label.setText(self.filename)
        layout.addWidget(self.label)

        return layout


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "file"

    print("Building application...")
    app = QtWidgets.QApplication([])
    window = SEMHelper(filename)

    print("Showing...")
    window.show()

    app.exec()
