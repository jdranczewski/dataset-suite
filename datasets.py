"""
A general data handling toolkit with a powerful class for abstracting away work
with multidimensional set.

Code by Jakub Dranczewski
jdranczewski.github.io
jbd17@ic.ac.uk
jakub.dranczewski@gmail.com
^ one of these will work

MIT License

Copyright (c) 2023 Jakub Dranczewski
Created as part of PhD work supported by the EU ITN EID project CORAL (GA no. 859841).

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
import os
import re
import pickle
import gzip
from glob import glob as _glob


def folders(folder="", rel_current=True):
    """
    Returns a list of folders within a specified directory. Current directory by default.
    Set rel_current to False to return just the folder names, instead of the full path
    relative to current directory.
    """
    if rel_current:
        return [os.path.join(*list(os.path.split(x)[:-1])) for x in glob(os.path.join(folder, "*", ""))]
    else:
        return [os.path.split(x)[-2] for x in glob(os.path.join(folder, "*", ""))]


def prefixes(folder, split, yes=[], no=[]):
    """
    Returns a list of file prefixes in a given folder that match some conditions.
    'prefix' is defined as the part of the filename before the string given as 'split'.
    'yes' and 'no' are lists/tuples or string that should/should not be in the full file
    name, so act as filters.
    """
    files = os.listdir(folder)
    for s in yes + [split]:
        files = [x for x in files if s in x]
    for s in no:
        files = [x for x in files if s not in x]
    prefixes = list(set([x.split(split)[0] for x in files]))
    prefixes.sort()
    return prefixes


def glob(path, yes=[], no=[]):
    """
    A small extension to the excellent glob library. 'path' is defined as for the usual
    glob: a Unix-style pathname with * as a wildcard.
    'yes' and 'no' are lists/tuples or string that should/should not be in the full file
    name, so act as filters.
    """
    files = _glob(path)
    for s in yes:
        files = [x for x in files if s in x]
    for s in no:
        files = [x for x in files if s not in x]
    files.sort()
    return files


def extract(string, *patterns):
    """
    Given a string and an arbitrary number of patterns as arguments, this function extracts
    associated numbers from the string. For example, '_P_' as a pattern will match '_P_123'
    in a filename and return 123.
    """
    return [int(re.search(pattern+"([0-9]+)", string).group(1)) for pattern in patterns]


def extract_raw(string, *patterns):
    """
    You can write regex? Good for you.
    Given a string and an arbitrary number of patterns as arguments, this function extracts
    associated things from the string. You have to include a capture group, otherwise errors ensue.
    """
    return [re.search(pattern, string).group(1) for pattern in patterns]


def extract_unique(files, pattern):
    numbers = list(set([extract(x, pattern)[0] for x in files]))
    numbers.sort()
    return numbers


def _sort_key(x, pattern):
    try:
        return int(re.search(pattern+"([0-9]+)", x).group(1))
    except AttributeError:
        return 1e10


def sort_by(files, pattern):
    """
    Given a list of strings (like file names or sth) and a pattern, the functions extracts
    an associated numeric parameter from each string and sorts the list according to that
    parameter.

    For example, if your files contain power information as '_P_123', pass '_P_' as 'pattern'.
    Sorting happens in-place in the passed list, so nothing is returned.
    """
    files.sort(key=lambda x:_sort_key(x, pattern))


def colours(values, cmap=None, minmax=None):
    # Check if matplotlib needs to be imported.
    # We only do this here, as this takes a bit of time, so it's silly to do this
    # every time the full library is imported.
    if 'cm' not in globals():
        global cm
        from matplotlib import cm

    # Default colourmap
    if cmap is None:
        cmap = cm.viridis

    if minmax is None:
        a, b = np.amin(values), np.amax(values)
    else:
        a, b = minmax

    if len(values) == 1:
        return cmap((0,))
    return cmap((values-a)/(b-a))


def map_axes(data, **axes):
    """
    Helper function for figuring out how the axes you have map to the data.
    data is the ndarray, and then you pass your axes in any order as keyword arguments.
    """
    data = np.asarray(data)
    shape = data.shape
    for s in shape:
        print(s, [key for key in axes if len(axes[key])==s])


def load(filename):
    with gzip.open(filename, 'rb') as f:
        return pickle.load(f)

        
class dataset():
    """
    A container for data with labelled axes.
    """
    def __init__(self, data, cut=None, **axes):
        self._raw = np.asarray(data)
        if len(axes) != self._raw.ndim:
            raise IndexError("The number of provided axes does not match the dataset.")
        for i, key in enumerate(axes):
            if self._raw.shape[i] != len(axes[key]):
                raise IndexError("The shape of the provided axes does not match the dataset.")
            setattr(self, key, np.asarray(axes[key]))
        self._axes = list(axes.keys())
        if cut is None:
            cut = {}
        self._cut = cut
        self.metadata = {}
        
    def take(self, **i):
        s_raw = self._raw
        cut = self._cut
        new_axes = self.ax_dict
        for key in i:
            s_raw = np.moveaxis(s_raw, self._axes.index(key), 0)[i[key]]
            cut[key] = self.axis(key)[i[key]]
            new_axes.pop(key)
        new_data = dataset(s_raw, cut=cut, **new_axes)
        new_data.metadata = self.metadata
        return new_data
    
    def take_raw(self, **i):
        s_raw = self._raw
        for key in i:
            s_raw = np.moveaxis(s_raw, self._axes.index(key), 0)[i[key]]
        return s_raw
    
    def take_sum(self, axis):
        new_axes = self.ax_dict
        new_axes.pop(axis)
        new_data = dataset(np.sum(self._raw, axis=self._axes.index(axis)), **new_axes)
        new_data.metadata = self.metadata
        return new_data
    
    def expand(self, new_axis, value):
        return dataset(np.expand_dims(self._raw, axis=0),
                       **{new_axis: [value], **self.ax_dict})
    
    def join(self, other, axis):
        new_axes = self.ax_dict
        new_axes[axis] = np.concatenate((self.axis(axis), other.axis(axis)))
        return dataset(np.concatenate((self._raw, other.raw), axis=self._axes.index(axis)),
                      **new_axes)
    
    def axis(self, ax):
        return getattr(self, ax)
    
    def astype(self, _type):
        new_data = dataset(self._raw.astype(_type), cut=self._cut, **self.ax_dict)
        new_data.metadata = self.metadata
        return new_data

    def save(self, filename, compress=6):
        with gzip.open(filename, 'wb', compresslevel=compress) as f:
            pickle.dump(self, f)
    
    @property
    def raw(self):
        return self._raw
    
    @property
    def axes(self):
        return self._axes
    
    @property
    def ax_dict(self):
        return {key: self.axis(key) for key in self._axes}
    
    @property
    def cut(self):
        return self._cut
    
    def add_cut(self, key, value):
        self._cut[key] = value
    
    def __repr__(self):
        return "dataset({})".format(", ".join("{}[{}]".format(key, len(self.axis(key))) for key in self._axes))


class datalist:
    def __init__(self, axis, cut=None):
        self._axes = [axis,]
        self._axis = []
        self._datasets = []
        setattr(self, axis, self._axis)
        if cut is None:
            cut = {}
        self._cut = cut
        self.metadata = {}
    
    def append(self, ds, value):
        ds.add_cut(self._axes[0], value)
        self._datasets.append(ds)
        self._axis.append(value)
    
    def add_cut(self, key, value):
        self._cut[key] = value
        for ds in self:
            ds.add_cut(key, value)
    
    def save(self, filename, compress=6):
        with gzip.open(filename, 'wb', compresslevel=compress) as f:
            pickle.dump(self, f)

    @property
    def axis(self):
        return self._axis
    
    @property
    def axes(self):
        return self._axes
    
    @property
    def datasets(self):
        return self._datasets
    
    @property
    def cut(self):
        return self._cut

    def __getitem__(self, i):
        return self._datasets[i]
    
    def __len__(self):
        return len(self._datasets)
    
    def __repr__(self):
        return str(self._datasets)
    

class datadict:
    def __init__(self, name, cut=None):
        self._name = name
        self._dict = {}
        if cut is None:
            cut = {}
        self._cut = cut
        self.metadata = {}
    
    def add_cut(self, key, value):
        self._cut[key] = value
        for element in self:
            try:
                self._dict[element].add_cut(key, value)
            except AttributeError:
                pass
    
    def save(self, filename, compress=6):
        with gzip.open(filename, 'wb', compresslevel=compress) as f:
            pickle.dump(self, f)
    
    @property
    def name(self):
        return self._name
    
    @property
    def dict(self):
        return self._dict
    
    @property
    def cut(self):
        return self._cut
    
    def __setitem__(self, key, value):
        try:
            value.add_cut(self._name, key)
        except AttributeError:
            pass

        self._dict[key] = value

    def __iter__(self):
        for key in self._dict:
            yield key
    
    def __getitem__(self, key):
        return self._dict[key]
    
    def __contains__(self, item):
        return item in self._dict
    
    def keys(self):
        return self._dict.keys()
    
    def __repr__(self):
        return "datadict({}: {})".format(self._name, ", ".join(self._dict.keys()))