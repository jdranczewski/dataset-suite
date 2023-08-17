from dataprocessor import DataProcessor
import sqlite3
import numpy as np
from superhuman import SuperParams
from io import BytesIO

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
sp = SuperParams("ET10s_new", param_spec)

class DBProcessor(DataProcessor):
    def run(self, dataset):
        fname = self.storage['dbname']
        self.storage['dbconn'] = dbconn = sqlite3.connect(fname)
        dbconn.row_factory = sqlite3.Row
        self.storage['dbcursor'] = dbconn.cursor()
        try:
            self.run_next(dataset)
        finally:
            dbconn.close()
            
class DBInitProcessor(DataProcessor):
    def run(self, dataset):
        self.storage['dbconn'].execute(self.storage['sp'].command_init())
        self.run_next(dataset)
            
class SavePeakProcessor(DataProcessor):
    def run(self, dataset):
        sp = self.storage['sp']
        # sp['indices'] = f"{dataset.cut['dpmeta_page']}, {dataset.cut['dpmeta_row']}, {dataset.cut['dpmeta_col']}"
        sp['indices'] = f"{dataset.cut['ix']}"
        sp['peak_location'] = self.storage['peak_location']
        sp['cut'] = str(dataset.cut)
        sp['fit_indices'] = self.storage['ll_fit_range']
        sp['threshold'] = self.storage['threshold']
        sp['threshold_error'] = self.storage['threshold_error']
        sp['threshold_wl'] = dataset.wl[self.storage['peak_location']]
        sp['ll_slope'] = self.storage['ll_slope']

        arr = np.vstack((dataset.power, self.storage['power_values'], self.storage['LL_values']))
        out = BytesIO()
        np.save(out, arr)
        out.seek(0)
        sp['arrays'] = out.read()
        
        self.storage['dbcursor'].execute(*sp.command_insert())
        self.storage['dbconn'].commit()
        
        if self.storage.get('plot_LL', False) and 'ax' in self.storage:
            self.storage['ax'].text(self.storage['threshold'], 0,
                                    "   " + str(self.storage['dbcursor'].lastrowid), size=8)
        
        self.run_next(dataset)