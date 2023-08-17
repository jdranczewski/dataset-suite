import spe_loader as sl
import os
import numpy as np

import datasets1 as ds

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from contextlib import nullcontext

def make_pdf(data, name=None):
    with (PdfPages(name) if name else nullcontext()) as pdf:
        for ds_kind in data:
            fig = None
            if isinstance(ds_kind[0], ds.datalist):
                shape = len(ds_kind), np.amax([len(x) for x in ds_kind])
                fig, ax = plt.subplots(shape[1], shape[0]*2, figsize=(shape[0]*5, shape[1]*3), sharex='col',
                                   constrained_layout=True, gridspec_kw={'width_ratios':[3,1]*shape[0]})
                ax = ax.reshape((shape[1],-1))
                fig.suptitle(", ".join((base, ds_kind.cut["wrap"])))
                for i, ds_device in enumerate(ds_kind):
                    ax[0,i*2].set_title(ds_device.cut["x"])
                    for j, dataset in enumerate(ds_device):
                        colours = ds.colours(dataset.power)
                        for k in range(len(dataset.power)):
                            ax[j,i*2].plot(dataset.wl, dataset.take_raw(power=k), c=colours[k], lw=1)
                        ax[j,i*2+1].plot(dataset.power[1:], dataset.take_sum('wl').raw[1:] ,"-")
                        ax[j,i*2].text(0.02, 0.95, dataset.cut["y"], va='top', transform=ax[j,i*2].transAxes)
                    for j in range(shape[1]):
                        ax[j,i*2+1].tick_params(labelleft=False)
            elif isinstance(ds_kind[0], ds.dataset):
                shape = len(ds_kind), np.amax([len(x.axis(x.axes[0])) for x in ds_kind])
                fig, ax = plt.subplots(shape[1], shape[0]*2, figsize=(shape[0]*5, shape[1]*3), sharex='col',
                                   constrained_layout=True, gridspec_kw={'width_ratios':[3,1]*shape[0]})
                ax = ax.reshape((shape[1],-1))
                for i, ds_device in enumerate(ds_kind):
                    ax[0,i*2].set_title(ds_device.cut["x"])
                    for j in range(len(ds_device.axis(ds_device.axes[0]))):
                        colours = ds.colours(ds_device.power)
                        for k in range(len(ds_device.power)):
                            ax[j,i*2].plot(ds_device.wl, ds_device.take_raw(power=k, x=j), c=colours[k], lw=1)
                        ax[j,i*2+1].plot(ds_device.power, ds_device.take(x=j).take_sum('wl').raw ,"-")
                        ax[j,i*2].text(0.02, 0.95, ds_device.x[j], va='top', transform=ax[j,i*2].transAxes)
                    for j in range(shape[1]):
                        ax[j,i*2+1].tick_params(labelleft=False)
            if pdf and fig:
                pdf.savefig(fig)


prefix = "prefix"
base = "folder"
files = ds.glob(os.path.join(base, prefix+"_X_*"), no=('raw',))

ds_wrapper = ds.datalist("wrap")
ds_main = ds.datalist("x")
for x in set([ds.extract(x, '_X_')[0] for x in files]):
    ds_x = ds.datalist("y")
    for y in set([ds.extract(x, '_Y_')[0] for x in files]):
        fnames = ds.glob(os.path.join(base, prefix+"_X_{}_Y_{}*".format(x, y)), no=('raw',))
        ds.sort_by(fnames, "_P_")
        ds_scan = None
        for fname in fnames:
            # print(x, y, P)
            # Get the laser power and integration time using their regex signatures
            P, I = ds.extract(fname, "_P_", "_I_")
            # Get the data out of the file
            # wls, counts = np.genfromtxt(file, delimiter=",", unpack=True, skip_header=1)
            spe_files = sl.load_from_files([fname])
            wls = spe_files.wavelength
            counts = np.squeeze(spe_files.data)
            counts /= I/100
            # Make a dataset and join it with the full power scan one. Need to add a 'power' axis for that, dim 1
            ds_single = ds.dataset(counts, wl=wls).expand('power', P/1000)
            if ds_scan:
                ds_scan = ds_scan.join(ds_single, "power")
            else:
                ds_scan = ds_single
        ds_x.append(ds_scan, y)
    ds_main.append(ds_x, x)
ds_wrapper.append(ds_main, 'yes')

print("making the pdf... ", end='')
make_pdf(ds_wrapper, os.path.join("pdfs", prefix+'.pdf'))
print("Done!")