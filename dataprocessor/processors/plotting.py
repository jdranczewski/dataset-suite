from dataprocessor import DataProcessor
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from contextlib import nullcontext
from tqdm.autonotebook import tqdm
import matplotlib.pyplot as plt


def make_page(self, d, pdf, i, name=None):
    # Make a Figure / page
    if pdf:
        self.storage['fig'] = fig = plt.Figure(constrained_layout=True)
    else:
        self.storage['fig'] = fig = plt.figure(constrained_layout=True)
    self.storage['r_i'] = 0
    self.storage['c_i'] = 0
    
    d.add_cut('dpmeta_page', i)
    self.run_next(d)
    
    c_set = set()
    r_set = set()
    for ax in fig.axes:
        n_rows, n_cols, start, stop = ax.get_subplotspec().get_geometry()
        c_set.add(n_cols)
        r_set.add(n_rows)
    
    gs = gridspec.GridSpec(ncols=max(c_set),
                            nrows=max(r_set), figure=fig)
    fig.set_size_inches(max(c_set)*2, max(r_set)*2)
    if name is not None:
        fig.suptitle(name)
    
    for ax in fig.axes:
        n_rows, n_cols, start, stop = ax.get_subplotspec().get_geometry()
        ax.set_subplotspec(gs[n_rows-1, n_cols-1])
#                 print(fig.get_size_inches())
    if pdf:
        pdf.savefig(fig)

class PdfPageProcessor(DataProcessor):
    def run(self, dataset):
        with (PdfPages(self.storage['pdf_name']) if self.storage['pdf_name'] else nullcontext()) as pdf:
            for i, (d, dname) in enumerate(zip(tqdm(dataset), dataset.axis)):
                make_page(self, d, pdf, i, f"{dataset.axes[0]}: {dname}")

class PdfPagePassthroughProcessor(DataProcessor):
    def run(self, dataset):
        with (PdfPages(self.storage['pdf_name']) if self.storage['pdf_name'] else nullcontext()) as pdf:
            make_page(self, dataset, pdf, 0)
                

class PlotGridProcessor(DataProcessor):
    def run(self, dataset):
        for i, d in enumerate(tqdm(dataset)):
            self.storage['r_i'] = i // 3
            self.storage['c_i'] = i % 3
            d.add_cut('dpmeta_row', i // 3)
            d.add_cut('dpmeta_col', i % 3)
            self.run_next(d)

class PlotRowsProcessor(DataProcessor):
    def run(self, dataset):
        # print('rows', len(dataset), dataset.cut)
        for i, d in enumerate(tqdm(dataset)):
            self.storage['r_i'] = i
            d.add_cut('dpmeta_row', i)
            self.run_next(d)
            
class PlotColsProcessor(DataProcessor):
    def run(self, dataset):
        # print('cols', len(dataset), dataset.cut)
        for i, d in enumerate(tqdm(dataset)):
            d.add_cut('dpmeta_col', i)
            self.storage['c_i'] = i
            self.run_next(d)

class PlotFirstColProcessor(DataProcessor):
    def run(self, dataset):
        # print('cols', len(dataset), dataset.cut)
        self.storage['c_i'] = 0
        self.run_next(dataset)

class PlotNextColProcessor(DataProcessor):
    def run(self, dataset):
        # print('cols', len(dataset), dataset.cut)
        self.storage['c_i'] += 1
        self.run_next(dataset) 

class MakeAxProcessor(DataProcessor):
    def run(self, dataset):
        # print('ax', dataset, dataset.cut)
        r_i, c_i = self.storage['r_i'], self.storage['c_i']
        self.storage['ax'] = self.storage['fig'].add_subplot(r_i + 1,
                                                             c_i + 1,
                                                             (r_i + 1) * (c_i + 1))
        ax = self.storage['ax']
        cut_text = ""
        for key in dataset.cut:
            if 'dpmeta' in key:
                continue
            if isinstance(dataset.cut[key], float):
                cut_text += f"{key}: {dataset.cut[key]:.2f}\n"
            else:
                cut_text += f"{key}: {dataset.cut[key]}\n"
        ax.text(.01, .99, cut_text, size=9, ha='left', va='top', transform=ax.transAxes)
        
        if self.storage.get('grid', False):
            ax.grid()
        
        self.run_next(dataset)