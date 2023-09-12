import matplotlib.pyplot as plt
import datasets as ds

def plot_ds(dataset, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = None
    
    assert len(dataset.axes) == 2
    y = dataset.axis(dataset.axes[0])
    x = dataset.axis(dataset.axes[1])
    c = ds.colours(y)

    for i in range(len(y)):
        ax.plot(x, dataset.raw[i,:], c=c[i])
    
    return fig, ax