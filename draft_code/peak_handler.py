import numpy as np
from scipy import signal
from sklearn.cluster import DBSCAN
from lmfit.models import LinearModel, Model

def trace_peaks(data):
    # Find all the peaks
    peaks = []
    for i in range(len(data.power)):
        I = data.take_raw(power=i)
        peaks_single, _ = signal.find_peaks(I, prominence=100)
        for peak in peaks_single:
            peaks.append([i, data.power[i], peak])
    peaks = np.array(peaks)
    
    # Group the peaks
    clustering = DBSCAN(eps=30, min_samples=2).fit(peaks[:,1:])
    
    # Return the peak traces
    return [peaks[np.where(clustering.labels_ == label)] for label in set(clustering.labels_) if label >= 0]

def complete_traces(traces, power):
    full = []
    for trace in traces:
        track_fit = np.poly1d(np.polyfit(*trace[:,1:].T, 1))
        trace_complete = track_fit(power)
        # trace_complete *= 0
        trace_complete[trace[:,0].astype(int)] = trace[:,2]
        full.append(trace_complete.astype(int))
    return full

def trace_intensities(trace, data):
    return np.array([data.take(power=i).take_raw(wl=trace[i]) for i in range(len(data.power))])

def softplus(x, a, b, c, d, k):
    return x*(a + b) + (a*np.log(np.exp(k*(c-x)) + 1))/k + d

def softplus_fit(x, I, k=30, first=4, last=3):
    # Naive fitting of two linear functions
    m = LinearModel()
    r = m.fit(I[:first], x=x[:first])
    r2 = m.fit(I[-last:], x=x[-last:])

    # Convert fitted params to a best guess for the softplus fit
    A, B, C, D = r.params['slope'].value, r.params['intercept'].value, r2.params['slope'].value, r2.params['intercept'].value
    k = 30
    a = C-A
    b = A
    c = np.log(np.exp(k*(B-D)/(C-A))-1)/k
    d = D

    # Fit the softplus
    m = Model(softplus)
    params = m.make_params(a=a, b=b, c=c, d=d, k=k)
    # params["c"].set(min=np.amin(x), max=np.amax(x))
    r = m.fit(I, params, x=x)

    return (np.log(np.exp(r.params['k'].value*r.params['c'].value)+1)/r.params['k'].value,
            {
                'result': r,
                'a0': r.params['b'].value,
                'b0': r.params['a'].value*np.log(np.exp(r.params['k'].value*r.params['c'].value)+1)/r.params['k'].value + r.params['d'].value,
                'a1': r.params['a'].value+r.params['b'].value,
                'b1': r.params['d'].value
            })

def threshold_wavelength(complete_trace, power, wl, threshold):
    track_fit = np.poly1d(np.polyfit(power, complete_trace, 1))
    return wl[int(np.round(track_fit(threshold)))]