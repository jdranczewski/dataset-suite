# from ast import Index
from pyqtgraph.Qt import QtCore, QtWidgets
import sqlite3


class SuperWidget(QtWidgets.QWidget):
    saveSignal = QtCore.Signal()
    closeSignal = QtCore.Signal()

    def __init__(self, dataset, params, name, *args, **kwargs):
        self.name = name
        self.dataset = dataset
        self.params = params

        super().__init__(*args, **kwargs)
        
        self.setWindowTitle(self.name)
        self.l = QtWidgets.QGridLayout()
        self.setLayout(self.l)

        self.l.addLayout(self.make_action_buttons(), 0, 0)
        self.l.addLayout(self.make_layout(), 1, 0)
    
    def make_action_buttons(self, spec=None):
        button_layout = QtWidgets.QHBoxLayout()

        _spec = [["Save", self.save]]
        if spec:
            spec = _spec + spec
        else:
            spec = _spec

        for button in spec:
            b = QtWidgets.QPushButton(button[0])
            b.clicked.connect(button[1])
            button_layout.addWidget(b)
        
        return button_layout

    def make_layout(self):
        return QtWidgets.QVBoxLayout()

    def save(self):
        self.saveSignal.emit()

    def closeEvent(self, *args, **kwargs):
        self.closeSignal.emit()
        super().closeEvent(*args, **kwargs)


class SuperWidgetTest(SuperWidget):
    def save(self):
        self.params['test'] = 1234
        return super().save()


class SuperParams:
    sqlite_types = {
        int: "INTEGER",
        str: "TEXT",
        float: "NUMERIC",
        sqlite3.Binary: "BLOB"
    }
    defaults = {
        int: "DEFAULT 0",
        str: "DEFAUTL ''",
        float: "DEFAULT 0.",
        sqlite3.Binary: ""
    }

    def __init__(self, name, params):
        self.name = name
        self._types = dict(params)
        self.params = self._types.keys()
        self._values = {key:None for key in self.params}

    def load_row(self, row):
        for key in row.keys():
            if not key == "id":
                self[key] = row[key]

    def command_init(self):
        text = 'CREATE TABLE IF NOT EXISTS "{}" ("id" INTEGER UNIQUE, '.format(self.name)
        for key in self.params:
            text += '"{}" {} {}, '.format(key, self.sqlite_types[self._types[key]], self.defaults[self._types[key]])
        text += 'PRIMARY KEY("id" AUTOINCREMENT));'
        return text

    def command_insert(self):
        text = 'INSERT INTO "{}" ({}) VALUES ({})'.format(self.name, ", ".join(self.params), ", ".join(['?']*len(self.params)))
        return text, [self._values[key] for key in self.params]

    def command_insert_update(self, id):
        s1 = 'INSERT OR IGNORE INTO "{}" (id) VALUES ({})'.format(self.name, int(id))
        update_string = ", ".join(["'{}'=?".format(x) for x in self.params])
        s2 = 'UPDATE {} SET {} WHERE id={}'.format(self.name, update_string, int(id))
        # print(s2)
        return s1, s2, [self._values[key] for key in self.params]

    def command_select(self, *keys):
        text = 'SELECT * FROM {} WHERE '.format(self.name)
        for key in keys:
            text += '"{}"=? AND '.format(key)
        return text[:-5]

    def __setitem__(self, key, value):
        if key not in self.params:
            raise KeyError("Trying to set a parameter '{}' that does not exist".format(key))
        if value is None:
            self._values[key] = None
        else:
            self._values[key] = self._types[key](value)
    
    def __getitem__(self, key):
        return self._values[key]
    
    def __repr__(self):
        return str(self._values)


class SuperCycler(QtWidgets.QWidget):
    def __init__(self, superwidget, datalist, dbconn, param_spec, name, *args, **kwargs):
        self.name = name
        self.superwidget = superwidget
        self.datalist = datalist
        self.dbconn = dbconn
        self.param_spec = param_spec

        self.init_db()

        super().__init__(*args, **kwargs)
        
        self.setWindowTitle(self.name)
        self.l = QtWidgets.QGridLayout()
        self.setLayout(self.l)

        self.l.addLayout(self.make_layout(), 0, 0)

    def make_layout(self):
        main_layout = QtWidgets.QVBoxLayout()

        self.next_b = QtWidgets.QPushButton("Next")
        self.next_b.clicked.connect(self.next)
        main_layout.addWidget(self.next_b)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(len(self.datalist))
        main_layout.addWidget(self.progress_bar)

        # On demand option
        od_layout = QtWidgets.QHBoxLayout()
        self.od_id = QtWidgets.QSpinBox()
        self.od_id.setMaximum(100000)
        od_layout.addWidget(self.od_id)
        self.od_b = QtWidgets.QPushButton("Redo")
        self.od_b.clicked.connect(self.on_demand)
        od_layout.addWidget(self.od_b)
        main_layout.addLayout(od_layout)

        return main_layout

    def init_db(self):
        sp = SuperParams(self.name, self.param_spec)
        self.dbconn.execute(sp.command_init())

    def next(self):
        self.next_b.setEnabled(False)
        self.od_b.setEnabled(False)
        self.od_id.setValue(0)
        self.od_id.setEnabled(False)

        try:
            args, data, params = self.make_advance()
            self.sw_instance = self.superwidget(*args, data, params, self.name)
            self.sw_instance.saveSignal.connect(self.save)
            self.sw_instance.closeSignal.connect(self.widget_closed)
            self.sw_instance.show()
        except ReferenceError:
            self.next()
            return
        # except IndexError:
        #     self.close()
        #     return
    
    def on_demand(self):
        params = SuperParams(self.name, self.param_spec)
        row = self.dbconn.execute(params.command_select('id'), (self.od_id.value(), )).fetchone()
        if row:
            params.load_row(row)
            args, data = self.get_from_row(row)

            self.next_b.setEnabled(False)
            self.od_b.setEnabled(False)
            self.od_id.setEnabled(False)

            self.sw_instance = self.superwidget(*args, data, params, self.name)
            self.sw_instance.saveSignal.connect(self.save)
            self.sw_instance.closeSignal.connect(self.widget_closed)
            self.sw_instance.show()


    def make_advance(self):
        # This one should be reimplemented when inherited
        if hasattr(self, 'i'):
            self.i += 1
        else:
            self.i = 0

        self.progress_bar.setValue(self.i+1)
        
        return [], self.datalist[self.i], SuperParams(self.name, self.param_spec)

    def get_from_row(self, row):
        raise NotImplementedError
    
    def save(self):
        if self.od_id.value() == 0:
            self.dbconn.execute(*self.sw_instance.params.command_insert())
        else:
            s1, s2, values = self.sw_instance.params.command_insert_update(self.od_id.value())
            self.dbconn.execute(s1)
            self.dbconn.execute(s2, values)
        self.dbconn.commit()
        self.sw_instance.close()

    def widget_closed(self):
        self.next_b.setEnabled(True)
        self.od_b.setEnabled(True)
        self.od_id.setEnabled(True)

    def bonus_args(self):
        return []


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    # window = SuperWidget(None, None, "Superhuman Test")
    # window.show()

    dbconn = sqlite3.connect('test.db')
    dbconn.row_factory = sqlite3.Row

    window = SuperCycler(SuperWidgetTest, [None, None], dbconn, {'test': int}, "SuperhumanTest")
    window.show()

    app.exec_()

    dbconn.close()
