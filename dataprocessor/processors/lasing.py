from dataprocessor import DataProcessor
import datasets1 as ds
import numpy as np
import scipy
from scipy import signal, interpolate
from lmfit import Model
from lmfit.models import PolynomialModel


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
            

class PL_Subtractor2:
    def __init__(self):
        pass

    def remove_peaks(self, I):
        I = I.copy()
        for repeat in range(10):
            pi = np.nanargmax(I)
            
            for i in range(pi, len(I)):
                if I[i] < I[pi]/2:
                    break
            i -= 1
            for j in range(pi, 0, -1):
                if I[j] < I[pi]/2:
                    break
            fwhm = i-j
            if fwhm > 20:
                break
            
            I[pi-3*fwhm:pi+3*fwhm] = np.nan
        return I

    def set_pl_from_datalist(self, datalist, window=71):
        avg_pl = np.nanmean([self.remove_peaks(d.take_raw(power=-1)) for d in datalist], axis=0)
        self.diff = np.convolve(avg_pl, [1/window]*window, mode='same') - avg_pl
        self._diff_wl = datalist[0].wl
        self._avg_pl = avg_pl
        
    def plot_pl_diff(self, ax):
        ax.plot(self._diff_wl, self._avg_pl)
        ax.plot(self._diff_wl, self._avg_pl + self.diff)
        ax.plot(self._diff_wl, self.diff)

    def find_boundaries(self, I, pi=None):
        """
        Establish the boundaries used for fitting and subtraction.
        Arguments should be a clear example of a peak (preferably at the highest power).
        """

        # Find the peak
        if pi is None:
            self.pi = pi = np.argmax(I)

        # Find the rough fwhm
        for i in range(pi, len(I)):
            if I[i] < I[pi]/2:
                break
        i -= 1
        for j in range(pi, 0, -1):
            if I[j] < I[pi]/2:
                break
        self.fwhm = i-j
        
        self.A = pi-3*self.fwhm-60
        self.B = pi-3*self.fwhm
        self.C = pi+3*self.fwhm
        self.D = pi+3*self.fwhm+60
    
    def subtract_pl(self, wl, I):
        model, params = self.get_model(wl, I)
        
        x = wl[self.B:self.C]
        return x, I[self.B:self.C] - model.eval(x=x, params=params)
    
    def get_model(self, wl, I):
        x = np.concatenate((wl[self.A:self.B], wl[self.C:self.D]))
        y = np.concatenate((I[self.A:self.B], I[self.C:self.D]))

        diff_interp = interpolate.interp1d(self._diff_wl, self.diff, bounds_error=False, fill_value=0)
        diff_fast = diff_interp(x)
        
        def absorption_fast(x, mult=1):
            # This ignores x, as it will always be the same during fitting
            return diff_fast*mult
        def absorption(x, mult=1):
            # This allows for arbitrary x
            diff = diff_interp(x)
            return diff*mult
        
        rm = PolynomialModel(5) + Model(absorption)
        m = PolynomialModel(5) + Model(absorption_fast)
        
        params = m.make_params(c0=np.mean(y), c1=0, c2=0, c3=0, c4=0, c5=0, mult=1)
        r = m.fit(y, x=x, params=params)
        
        return rm, r.params


class MakePLSProcessor(DataProcessor):
    def run(self, dataset):
        self.storage['pls'] = pls = PL_Subtractor2()
        pls.set_pl_from_datalist(dataset)
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

class DividePowerProcessor(DataProcessor):
    def run(self, dataset):
        self.storage['power'] = dataset.power/100.
        self.run_next(dataset)

class ConvertPowerProcessor(DataProcessor):
    def __init__(self, pipeline=None, storage=None):
        percent, pW = np.genfromtxt(storage['power_file'], delimiter=',', unpack=True)
        percent /= 100
        pJpp = pW/78e6*1e12
        self.p_to_power = np.poly1d(np.polyfit(percent, pJpp, 3))

        super().__init__(pipeline, storage)

    def run(self, dataset):
        power = self.storage.get('power', dataset.power)
        self.storage['power_values'] = self.p_to_power(power)
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
