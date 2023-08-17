import superhuman
import superparamore
import datasets1 as ds

import numpy as np
import sqlite3
from io import BytesIO
import skimage.io
import os

from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg


class SuperEtchtest(superhuman.SuperWidget):
    def __init__(self, dbconn, filename, params, name, *args, **kwargs):
        self.dbconn = dbconn
        self.image = skimage.io.imread((ds.glob(filename+'*', yes=('.tif')) + ds.glob(filename+'*', yes=('.jpg')))[0]).T
        self.pixelsize = None
        with open(filename+'.txt', 'r') as f:
            for line in f:
                if 'PixelSize' in line:
                    self.pixelsize = float(line.split("=")[1])
        if not self.pixelsize:
            raise ValueError("No metadata for the image resolution")
        super().__init__(filename, params, name, *args, **kwargs)
        self.showMaximized()

    def make_action_buttons(self, spec=None):
        spec = [['Skip', self.skip]]
        return super().make_action_buttons(spec)

    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel()
        label.setText(self.dataset)
        layout.addWidget(label, 0, 0)

        self.left_check = QtWidgets.QCheckBox("Left edge")
        layout.addWidget(self.left_check, 0, 1)

        imv = pg.ImageView()
        layout.addWidget(imv, 1, 0)
        imv.setImage(self.image)

        self.controls = {
            "mask_top": pg.InfiniteLine(300, 0, movable=True),
            "filth_top": pg.InfiniteLine(200, 0, movable=True, pen=(255,0,255)),
            "target_top": pg.TargetItem((150,250), pen=(255,0,0)),
            "line_top": pg.InfiniteLine(250, 0, pen=(255,0,0,100)),
            "target_bottom": pg.TargetItem((250,150), pen=(0,0,255)),
            "line_bottom": pg.InfiniteLine(150, 0, pen=(0,0,255,100)),
            "side": pg.PlotDataItem((150,250), (250,150), pen=(50,50,50))
        }
        for key in self.controls:
            imv.addItem(self.controls[key])
        self.controls["target_top"].sigPositionChanged.connect(self.targets_updated)
        self.controls["target_bottom"].sigPositionChanged.connect(self.targets_updated)

        inputs_layout = self.params.generate_layout()
        layout.addLayout(inputs_layout, 1, 1)

        # recipe name autocomplete
        try:
            cursor = self.dbconn.execute("SELECT DISTINCT recipe_name as r FROM {} ORDER BY r".format(self.name))
            recipes = [x['r'] for x in cursor]
            if len(recipes):
                completer = QtWidgets.QCompleter(recipes, self)
                completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
                self.params._inputs["recipe_name"].textbox.setCompleter(completer)
        except AttributeError:
            # Allow this to function without a database
            pass

        layout.setColumnStretch(0, 2)
        layout.setColumnStretch(1, 1)

        return layout

    def targets_updated(self):
        xt, yt = self.controls["target_top"].pos()
        xb, yb = self.controls["target_bottom"].pos()
        self.controls["line_top"].setValue(yt)
        self.controls["line_bottom"].setValue(yb)
        self.controls["side"].setData((xb, xt), (yb, yt))

    def save(self):
        self.params.save()

        self.params['skip'] = 0
        self.params['filename'] = self.dataset
        self.params['scale'] = self.pixelsize

        xt, yt = self.controls["target_top"].pos()
        xb, yb = self.controls["target_bottom"].pos()
        self.params['mask_depth'] = (self.controls["mask_top"].value() - yt) * self.pixelsize
        self.params['filth_depth'] = (self.controls["filth_top"].value() - yb) * self.pixelsize
        self.params['etch_depth'] = (yt - yb) * self.pixelsize
        self.params['wall_distance'] = (xb - xt) * self.pixelsize
        self.params['wall_angle'] = (np.arctan2(xb-xt, yt-yb))*180/np.pi

        flipped = -1 if self.left_check.isChecked() else 1
        self.params["wall_distance"] *= flipped
        self.params["wall_angle"] *= flipped

        return super().save()

    def skip(self):
        self.params.save()

        self.params['skip'] = 1
        self.params['filename'] = self.dataset

        return super().save()

class EtchCycler(superhuman.SuperCycler):
    def __init__(self, superwidget, datalist, dbconn, param_spec, name, *args, **kwargs):
        self.i = 0
        super().__init__(superwidget, datalist, dbconn, param_spec, name, *args, **kwargs)

    def init_db(self):
        sp = superparamore.SuperParamore(self.name, self.param_spec)
        self.dbconn.execute(sp.command_init())
    
    def make_advance(self):
        params = superparamore.SuperParamore(self.name, self.param_spec)

        self.progress_bar.setValue(self.i+1)
        self.i += 1

        cursor = self.dbconn.execute(params.command_select('filename'), (self.datalist[self.i-1],))
        if cursor.fetchone():
            raise ReferenceError("This dataset has been processed already")

        return [self.dbconn], self.datalist[self.i-1], params

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    dbconn = sqlite3.connect('etch_test.db')
    dbconn.row_factory = sqlite3.Row

    paramore_spec = {
        'filename': {'value': str},
        'skip': {'value': int},
        'sample': {'value': str, 'input': 'text'},
        'sample_type': {'value': str, 'input': 'dropdown', 'options': ['bulk', 'bonded120', 'bonded150']},
        'recipe_name': {'value': str, 'input': 'text'},
        'conditioning': {'value': int, 'input': 'time'},
        'time': {'value': int, 'input': 'time'},
        'cycles': {'value': int, 'input': 'int'},
        'pressure': {'value': float, 'input': 'float'},
        'temperature': {'value': str, 'input': 'dropdown', 'options': ['20', '80']},
        'rf_power': {'value': int, 'input': 'int'},
        'dc_bias': {'value': int, 'input': 'int'},
        'icp_power': {'value': int, 'input': 'int'},
        'Cl2': {'value': float, 'input': 'float'},
        'CH4': {'value': float, 'input': 'float'},
        'H2': {'value': float, 'input': 'float'},
        'Ar': {'value': float, 'input': 'float'},
        'N2': {'value': float, 'input': 'float'},
        'cleaning': {'value': int, 'input': 'check'},
        'scale': {'value': float},
        'initial_mask': {'value': float, 'input': 'float'},
        'mask_depth': {'value': float},
        'etch_depth': {'value': float},
        'filth_depth': {'value': float},
        'wall_distance': {'value': float},
        'wall_angle': {'value': float},
        'defects': {'value': str, 'input': 'multi', 'options': ['trenching', 'micromasking', 'microdeposits', 'surface', 'tails', 'mask_gone', 'walls_rough', 'wall_deposits', 'undercut', 'dirt']},
        'comment': {'value': str, 'input': 'text'}
    }

    base = 'folder'
    files = [os.path.join(base, x) for x in ds.prefixes(base, '.')]
    ds.sort_by(files, 'OM')
    window = EtchCycler(SuperEtchtest, files, dbconn, paramore_spec, 'DoE_etchtests')
    window.show()

    app.exec_()

    #dbconn.close()