from superhuman import SuperParams
from pyqtgraph.Qt import QtCore, QtWidgets

class ParamoreInput:
    def __init__(self, name, spec, *args, **kwargs):
        self.spec = spec

        self.label = QtWidgets.QLabel()
        self.label.setText(name+':')

        self.input_layout = self.make_input_layout()
    
    def make_input_layout(self):
        return QtWidgets.QHBoxLayout()
    
    def setValue(self, value):
        raise NotImplementedError

    def getValue(self):
        raise NotImplementedError

class StringInput(ParamoreInput):
    def make_input_layout(self):
        layout = super().make_input_layout()
        self.textbox = QtWidgets.QLineEdit()
        layout.addWidget(self.textbox)
        return layout
    
    def getValue(self):
        return self.textbox.text()

class DropdownInput(ParamoreInput):
    def make_input_layout(self):
        layout = super().make_input_layout()
        self.dropdown = QtWidgets.QComboBox()
        for item in self.spec['options']:
            self.dropdown.addItem(item)
        layout.addWidget(self.dropdown)
        return layout

    def getValue(self):
        return self.dropdown.currentText()

class TimeInput(ParamoreInput):
    def make_input_layout(self):
        layout = QtWidgets.QHBoxLayout()
        self.minutes = QtWidgets.QSpinBox()
        self.seconds = QtWidgets.QSpinBox()
        layout.addWidget(self.minutes)
        layout.addWidget(self.seconds)
        return layout

    def getValue(self):
        return self.minutes.value()*60 + self.seconds.value()

class IntInput(ParamoreInput):
    def make_input_layout(self):
        layout = QtWidgets.QHBoxLayout()
        self.number = QtWidgets.QSpinBox()
        self.number.setMaximum(100000)
        layout.addWidget(self.number)
        return layout

    def getValue(self):
        return self.number.value()

class FloatInput(ParamoreInput):
    def make_input_layout(self):
        layout = QtWidgets.QHBoxLayout()
        self.number = QtWidgets.QDoubleSpinBox()
        self.number.setMaximum(100000)
        layout.addWidget(self.number)
        return layout

    def getValue(self):
        return self.number.value()

class CheckInput(ParamoreInput):
    def make_input_layout(self):
        layout = QtWidgets.QHBoxLayout()
        self.check = QtWidgets.QCheckBox()
        layout.addWidget(self.check)
        return layout
    
    def getValue(self):
        return int(self.check.isChecked())

class MultiInput(ParamoreInput):
    def make_input_layout(self):
        layout = QtWidgets.QVBoxLayout()
        self.checks = []
        for item in self.spec['options']:
            self.checks.append(QtWidgets.QCheckBox(item))
            layout.addWidget(self.checks[-1])
        return layout
    
    def getValue(self):
        options = self.spec['options']
        return ",".join([options[i] for i in range(len(options)) if self.checks[i].isChecked()])

inputs = {
    'text': StringInput,
    'dropdown': DropdownInput,
    'time': TimeInput,
    'int': IntInput,
    'float': FloatInput,
    'check': CheckInput,
    'multi': MultiInput
}

class SuperParamore(SuperParams):
    def __init__(self, name, paramore_spec):
        self._paramore_spec = dict(paramore_spec)
        params = {key:paramore_spec[key]['value'] for key in paramore_spec}
        self._inputs = {key:None for key in paramore_spec}
        super().__init__(name, params)
    
    def generate_layout(self):
        layout = QtWidgets.QGridLayout()

        i = 0
        for param in self._paramore_spec:
            spec = self._paramore_spec[param]
            if 'input' not in spec:
                continue
            paramore_input = inputs[spec['input']](param, spec)
            layout.addWidget(paramore_input.label, i, 0)
            layout.addLayout(paramore_input.input_layout, i, 1)
            self._inputs[param] = paramore_input
            i += 1

        return layout

    def save(self):
        for param in self.params:
            if self._inputs[param]:
                self[param] = self._inputs[param].getValue()


class SuperParamoreFake(dict):
    def __init__(self, name, paramore_spec):
        super().__init__()
        
    def generate_layout(self):
        pass
    
    def save(self):
        pass
