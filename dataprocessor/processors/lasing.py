from dataprocessor import DataProcessor
import datasets1 as ds
import numpy as np
import scipy
from scipy import signal


class SpectraProcessor(DataProcessor):
    def run(self, dataset):
        ax = self.storage['ax']
        colours = ds.colours(dataset.power)
        for i in range(len(dataset.power)):
            ax.plot(dataset.wl, dataset.take_raw(power=i), c=colours[i])
        self.storage['spectra_plotted'] = True
        self.run_next(dataset)
            
class SumProcessor(DataProcessor):
    def run(self, dataset):
        ax = self.storage['ax']
        ax.plot(dataset.power, dataset.take_sum('wl').raw)
        ax.loglog()
        self.run_next(dataset)

class FindPeaksProcessor(DataProcessor):
    def run(self, dataset, I=None):
        prominence = self.storage['peak_prominence'] if 'peak_prominence' in self.storage else 1000
        if I is None:
            I = dataset.take_raw(power=-1)
        peaks, _ = signal.find_peaks(I, prominence=prominence)
        
        if self.storage.get('plot_peaks', False) and 'ax' in self.storage:
            if not self.storage.get("spectra_plotted", False):
                self.storage['ax'].plot(dataset.wl, I)
            self.storage['ax'].plot(dataset.wl[peaks], I[peaks], 'x')
            # self.storage['ax'].plot([dataset.wl[0], dataset.wl[-1]], [np.mean(I[peaks])]*2)
            
        for peak in peaks:
            self.storage['peak_location'] = int(peak)
            self.storage['pls'].find_boundaries(I, pi=peak)
            if self.storage['pls'].fwhm < 20:
                if self.storage.get('plot_peaks', False) and 'ax' in self.storage:
                    self.storage['ax'].text(dataset.wl[peak], I[peak], str(self.storage['pls'].fwhm))
                self.run_next(dataset)
            

class PLSubProcessor(DataProcessor):
    def run(self, dataset):
        pls = self.storage['pls']
        power = self.storage.get("power_values", dataset.power)
        values = []
        for j in range(len(dataset.power)):
            x, y = pls.subtract_pl(dataset.wl, dataset.take_raw(power=j))
            values.append(np.sum(y))
        self.storage['LL_values'] = values
            
        if self.storage.get('plot_LL', False) and 'ax' in self.storage:
            self.storage['ax'].plot(power, values)
#             self.storage['ax'].loglog()
        self.run_next(dataset)
  
class DummySubProcessor(DataProcessor):
    """
    A silly test
    """
    def run(self, dataset):
        pls = self.storage['pls']
        values = []
        for j in range(len(dataset.power)):
            values.append(np.sum(dataset.take_raw(power=j)[self.storage['pls'].B:self.storage['pls'].C]))
        self.storage['LL_values'] = values
            
        if self.storage.get('plot_LL', False) and 'ax' in self.storage:
            self.storage['ax'].plot(dataset.power, values)
#             self.storage['ax'].loglog() 
        self.run_next(dataset)

class ConvertPowerProcessor(DataProcessor):
    def __init__(self, pipeline=None, storage=None):
        percent, pW = np.genfromtxt(storage['power_file'], delimiter=',', unpack=True)
        percent /= 100
        pJpp = pW/78e6*1e12
        self.p_to_power = np.poly1d(np.polyfit(percent, pJpp, 3))

        super().__init__(pipeline, storage)

    def run(self, dataset):
        self.storage['power_values'] = self.p_to_power(dataset.power)
        self.run_next(dataset)

# Trying to figure out the inflection point thing
class InflectionProcessor(DataProcessor):
    def run(self, dataset):
        I = self.storage['LL_values']
        power = self.storage.get("power_values", dataset.power)
        slopes = []

        expand = 3
        if len(power) <= expand*2:
            print("Inflection point could not be found for ", dataset.cut)
            return
        for centre in range(expand, len(power)-3):
            x = power[centre-expand:centre+expand+1]
            y = I[centre-expand:centre+expand+1]
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
            slopes.append(slope)        
        
        if self.storage.get('plot_LL', False) and 'ax' in self.storage:
            sm = np.argmax(slopes) + 3
            self.storage['inflection'] = sm
            self.storage['ax'].plot(power[sm], I[sm], 'x')
            
        self.run_next(dataset)

class ThresholdProcessor(DataProcessor):
    def run(self, dataset):
        I = self.storage['LL_values']
        power = self.storage.get("power_values", dataset.power)
        
        if 'inflection' not in self.storage:
            # Get the inflection point from a smoothed curve
            window = 11
            pc = np.convolve(power, [1/window]*window, mode='valid')
            Ic = np.convolve(I, [1/window]*window, mode='valid')

            der = Ic[1:]-Ic[:-1]
            centre = np.argmax(der) + window//2 + 1
        else:
            centre = self.storage['inflection']
        if centre >= len(power):
            centre = len(power)-1
        end = 15 if centre>15 else centre+1
        
        # Fit linear functions repeatedly
        error = []
        for expand in range(2, end):
#             print(centre, expand, centre-expand, len(power))
            x = power[centre-expand:centre+expand+1]
            y = I[centre-expand:centre+expand+1]
#             print(x, y)
            fit, p = np.polyfit(x, y, 1, cov=True)
            error.append((np.sqrt(p[0,0])/abs(fit[0]) + np.sqrt(p[1,1])/abs(fit[1])) * -(fit[1]/fit[0]))
            
        # Choose the fit with the smallest threshold error
        expand = np.argmin(error) + 2
        
        x = power[centre-expand:centre+expand+1]
        y = I[centre-expand:centre+expand+1]
        self.storage['ll_fit_range'] = f"{centre-expand}:{centre+expand+1}"
        fit, p = np.polyfit(x, y, 1, cov=True)
        self.storage['threshold'] = threshold = -(fit[1]/fit[0])
        self.storage['ll_slope'] = fit[0]
        self.storage['threshold_error'] = (np.sqrt(p[0,0])/abs(fit[0]) + np.sqrt(p[1,1])/abs(fit[1])) * -(fit[1]/fit[0])
        
        if self.storage.get('plot_LL', False) and 'ax' in self.storage:
            ax = self.storage['ax']
            xx = np.linspace(-(fit[1]/fit[0]), x[-1])     
            ax.plot(x, y, 'o-', ms=3)
            ax.plot(xx, np.poly1d(fit)(xx))

            ax.plot(power[centre], I[centre], 'o', ms=3)
        self.run_next(dataset)
