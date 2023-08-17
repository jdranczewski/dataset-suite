from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np


class dbPlotter(QtWidgets.QWidget):
    def __init__(self, file):
        super().__init__()
        self.file = file
        self.x = np.array([])
        self.y=np.array([])

        self.setWindowTitle("OSA Plotter")
        self.l = self.make_layout()
        self.setAcceptDrops(True)
        self.setLayout(self.l)

        self.thread = QtCore.QThread()

        self.read_file()

    def make_layout(self):
        layout = QtWidgets.QGridLayout()

        button = QtWidgets.QPushButton("Select File")
        button.clicked.connect(self.select)
        layout.addWidget(button, 0, 0)


        self.pw = pg.PlotWidget()
        self.plot = self.pw.getPlotItem()
        self.plot.showGrid(x=True, y=True)
        #self.line = self.plot.plot([0,1], [0,0])
        layout.addWidget(self.pw, 1, 0, 1, 2)
    

        return layout

    def select(self,):
        self.file = QtWidgets.QFileDialog.getOpenFileName(self,"Open file","""C:\\""",)[0]
        print(self.file)
        self.read_file()

    def read_file(self):
        with open(self.file) as file:
            lines=file.readlines()
        try:
            matrix=np.array([line.split(',') for line in lines[8:]]).astype(float)
            assert(matrix.shape[1] == 2)
        except Exception as e:
            dlg=QtWidgets.QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText("File has incompatible layout")
            print(e)
            dlg.exec()
            return
            

        self.x = matrix[:,0]
        self.y = matrix[:,1]

        self.update_plot()
    
    def update_plot(self):
        self.plot.clear()
        self.plot.plot(self.x,self.y)




if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = dbPlotter("""file""")
    window.show()

    app.exec_()