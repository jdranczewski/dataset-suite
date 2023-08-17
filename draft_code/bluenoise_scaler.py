# %matplotlib notebook
import numpy as np
import matplotlib.pyplot as plt
from tqdm.autonotebook import tqdm

from utils import mnist_reader

X_test, y_test = mnist_reader.load_mnist('data/fashion', kind='t10k')

X_test.shape

# +
fig, ax = plt.subplots(5, 5)
ax = ax.flatten()

for i in range(25):
    ax[i].imshow(X_test[i].reshape((28, 28)), cmap='Greys')
#     ax[i].axis('off')
# -

# # Transform

import skimage.transform

# +
fig, ax = plt.subplots(2, 3)

a = X_test[4].reshape((28, 28)) / 255
a_scaled = skimage.transform.rescale(a, 7, order=0)
a_scaled_i = skimage.transform.rescale(a, 7, order=1)
ax[0, 0].imshow(a, cmap='Greys')
ax[0, 1].imshow(a_scaled, cmap='Greys')
ax[0, 2].imshow(a_scaled_i, cmap='Greys')
ax[1, 0].imshow(a>.5, cmap='Greys')
ax[1, 1].imshow(a_scaled>.5, cmap='Greys')
ax[1, 2].imshow(a_scaled_i>0.5, cmap='Greys')
# +
def fill_fs(array):
    N, N = array.shape
    arr = np.zeros((N+2,N+2))
    arr[1:-1, 1:-1] = array.copy()
    for y in range(1,N+1):
        for x in range(1,N+1):
            old = arr[x,y]
            new = np.round(old)
            arr[x,y] = new
            quant_error = old - new
            arr[x-1:x+2, y:y+2] += quant_error/16 * np.array([[0, 0, 7],[3, 5, 1]]).T
    return arr[1:-1, 1:-1]

def fill_jjn(array):
    N, N = array.shape
    arr = np.zeros((N+4,N+4))
    arr[2:-2, 2:-2] = array.copy()
    for y in range(2,N+2):
        for x in range(2,N+2):
            old = arr[x,y]
            new = np.round(old)
            arr[x,y] = new
            quant_error = old - new
            arr[x-2:x+3, y:y+3] += quant_error/48 * np.array([[0, 0, 0, 7, 5],[3, 5, 7, 5, 3], [1, 3, 5, 3, 1]]).T
    return arr[2:-2, 2:-2]


# +
fig, ax = plt.subplots(3, 3, sharex=True, sharey=True)

ax[0, 0].imshow(a, cmap='Greys')
ax[0, 1].imshow(a_scaled, cmap='Greys')
ax[0, 2].imshow(a_scaled_i, cmap='Greys')
ax[1, 0].imshow(fill_fs(a), cmap='Greys')
ax[1, 1].imshow(fill_fs(a_scaled), cmap='Greys')
ax[1, 2].imshow(fill_fs(a_scaled_i), cmap='Greys')
ax[2, 0].imshow(fill_jjn(a), cmap='Greys')
ax[2, 1].imshow(fill_jjn(a_scaled), cmap='Greys')
ax[2, 2].imshow(fill_jjn(a_scaled_i), cmap='Greys')
# -

print(7*7, "total valid values")
print(255, "values in dataset")
print(49/255, "max error")

d = fill_fs(a_scaled)
ds = np.zeros((28, 28))
for i in range(28):
    for j in range(28):
#         print(i, j)
#         print(i*7, (i+1)*7, j*7+(j+1)*7)
        ds[i, j] = np.sum(d[i*7:(i+1)*7, j*7:(j+1)*7])/49

fig, ax = plt.subplots(1, 3)
ax[0].imshow(a)
ax[1].imshow(ds)
ax[2].imshow((ds-a)/a)

np.nanmax((ds-a)/a, )

# # Validating dithering shape

a = np.arange(49).reshape(7,7)/48
fig, ax = plt.subplots(2, 3)
a_scaled = skimage.transform.rescale(a, 7, order=0)
a_scaled_i = skimage.transform.rescale(a, 7, order=1)
ax[0, 0].imshow(a, cmap='Greys')
ax[0, 1].imshow(a_scaled, cmap='Greys')
ax[0, 2].imshow(a_scaled_i, cmap='Greys')
ax[1, 0].imshow(a>.5, cmap='Greys')
ax[1, 1].imshow(a_scaled>.5, cmap='Greys')
ax[1, 2].imshow(a_scaled_i>0.5, cmap='Greys')

# +
fig, ax = plt.subplots(3, 2, sharex=True, sharey=True)

ax[0, 0].imshow(a_scaled, cmap='Greys')
ax[0, 1].imshow(a_scaled_i, cmap='Greys')
ax[1, 0].imshow(fill_fs(a_scaled), cmap='Greys')
ax[1, 1].imshow(fill_fs(a_scaled_i), cmap='Greys')
ax[2, 0].imshow(fill_jjn(a_scaled), cmap='Greys')
ax[2, 1].imshow(fill_jjn(a_scaled_i), cmap='Greys')

for axis in ax.flatten():
    for i in range(8):
        axis.plot([i*7-0.5, i*7-0.5], [0-0.5, 7*7-0.5])
        axis.plot([0-0.5, 7*7-0.5], [i*7-0.5, i*7-0.5])
# -

# # Blue noise?

from skimage.io import imread
blue = imread("../HDR_L_0.png")/(2**16-1)

small_blue = blue[10:17, 10:17]

# +
fig, ax = plt.subplots(1, 2)

ax[0].imshow(small_blue)

sbr = small_blue.reshape((1, -1))[0]
ordered = np.zeros(sbr.shape)
for i, arg in enumerate(np.argsort(sbr)):
    ordered[arg] = i
ordered_img = ordered.reshape((7,7))
ax[1].imshow(ordered_img)
# -

fig, ax = plt.subplots(7,7)
ax = ax.flatten()
for i in range(49):
    ax[i].imshow(ordered_img>i)
    ax[i].axis('off')

fig, ax = plt.subplots(7,7)
ax = ax.flatten()
for i in range(49):
    x, y = np.random.randint(0, 256-7), np.random.randint(0, 256-7)
    small_blue = blue[x:x+7, y:y+7]
    sbr = small_blue.reshape((1, -1))[0]
    
    ordered = np.zeros(sbr.shape)
    args = np.argsort(sbr)
    ordered[args[:i]] = 1
    
    ordered_img = ordered.reshape((7,7))
    
    ax[i].imshow(ordered_img)
    ax[i].axis('off')

# ## Profile this solution

value = 15

# %load_ext snakeviz

# +
# %%timeit

small_blue = blue[10:17, 10:17]
sbr = small_blue.reshape((1, -1))[0]
ordered = np.zeros(sbr.shape)
args = np.argsort(sbr)
ordered[args[args<value]] = 1
ordered_img = ordered.reshape((7,7))
result = ordered_img > value
# -

17.2e-6*7*7*10000

# # Implement

a = np.arange(49).reshape(7,7)/49
mult = 7

from numba import jit


# @jit(nopython=True)
def get_pixel(value, mult):
    x, y = np.random.randint(0, 256-mult), np.random.randint(0, 256-mult)
    # x, y = 0, 0
    small_blue = blue[x:x+mult, y:y+mult]
    sbr = small_blue.reshape((1, mult**2))[0]
    
    final = np.zeros(sbr.shape)
    args = np.argsort(sbr)
    final[args[:value]] = 1
    
    return final.reshape((mult,mult))


@jit(nopython=True)
def get_pixel(value, mult):
    x, y = np.random.randint(0, 256-mult), np.random.randint(0, 256-mult)
    # x, y = 0, 0
    small_blue = np.ascontiguousarray(blue[x:x+mult, y:y+mult])
    sbr = small_blue.reshape((1, mult**2))[0]
    
    final = np.zeros(sbr.shape)
    args = np.argsort(sbr)
    final[args[:value]] = 1
    
    return final.reshape((mult,mult))


def multiplex(array, mult):
    array_rounded = np.round(array*(mult**2)).astype(int)
    w, h = array_rounded.shape
    final = np.zeros((w*mult, h*mult))
    for x in range(w):
        for y in range(h):
            final[x*mult:(x+1)*mult, y*mult:(y+1)*mult] = get_pixel(array_rounded[x, y], mult)
    return final


@jit(nopython=True)
def get_pixel_position(value, mult, x, y):
    x, y = x*mult, y*mult
    small_blue = np.ascontiguousarray(blue[x:x+mult, y:y+mult])
    sbr = small_blue.reshape((1, mult**2))[0]
    
    final = np.zeros(sbr.shape)
    args = np.argsort(sbr)
    final[args[:value]] = 1
    
    return final.reshape((mult,mult))


def multiplex_deterministic(array, mult):
    array_rounded = np.round(array*(mult**2)).astype(int)
    w, h = array_rounded.shape
    final = np.zeros((w*mult, h*mult))
    for x in range(w):
        for y in range(h):
            final[x*mult:(x+1)*mult, y*mult:(y+1)*mult] = get_pixel_position(array_rounded[x, y], mult, x, y)
    return final


# +
fig, ax = plt.subplots()
mult = 5
a = np.arange(mult**2).reshape(mult,mult)/mult**2
ax.imshow(multiplex_deterministic(a, mult))

for i in range(mult):
    ax.plot([i*mult-0.5, i*mult-0.5], [0-0.5, mult*mult-0.5])
    ax.plot([0-0.5, mult*mult-0.5], [i*mult-0.5, i*mult-0.5])
# -

# # Try on the MNIST

# +
fig, ax = plt.subplots(2, 3, sharex=True, sharey=True, constrained_layout=True)

a = X_test[4].reshape((28, 28)) / 255
a_scaled = skimage.transform.rescale(a, 7, order=0)

# 'Floyd - Steinberg' and 'Minimized average error dithering' by Jarvis, Judice, and Ninke

ax[0, 0].imshow(a_scaled, cmap="Greys")
ax[0, 0].set_title("Data")

ax[1, 1].imshow(multiplex(a, 7), cmap="Greys")
ax[1, 1].set_title("Blue noise (rnd)")
ax[1, 2].imshow(a_scaled>blue[:196, :196], cmap="Greys")
ax[1, 2].set_title("Blue noise (th)")
ax[1, 0].imshow(multiplex_deterministic(a, 7), cmap="Greys")
ax[1, 0].set_title("Blue noise (det)")

ax[0, 1].imshow(fill_fs(a_scaled), cmap='Greys')
ax[0, 1].set_title("Floyd - Steinberg")
ax[0, 2].imshow(fill_jjn(a_scaled), cmap='Greys')
ax[0, 2].set_title("Jarvis, Judice, and Ninke")
# -

# ## Compare errors

# +
# %%snakeviz

for f, desc, array in zip((fill_fs, fill_jjn, lambda x: multiplex(x, 7)), 
                          ("FS", "JJN", "Blue"),
                          (a_scaled, a_scaled, a)):
    d = f(array)
    ds = np.zeros((28, 28))
    for i in range(28):
        for j in range(28):
            ds[i, j] = np.sum(d[i*7:(i+1)*7, j*7:(j+1)*7])/49
            
#     print(np.mean(d), np.mean(ds))
    print(desc, np.nanmax((ds-a)), np.nanmean((ds-a)))

# +
fig, ax = plt.subplots(2, 2, sharex=True, sharey=True)

a = X_test[0].reshape((28, 28)) / 255
a_scaled = skimage.transform.rescale(a, 7, order=0)

ax[0, 0].imshow(a_scaled, cmap="Greys")
ax[0, 1].imshow(multiplex(a, 7), cmap="Greys")
ax[1, 0].imshow(fill_fs(a_scaled), cmap='Greys')
ax[1, 1].imshow(fill_jjn(a_scaled), cmap='Greys')

# ax[]
# -

def downsample(array, mult):
    ds = np.zeros((28, 28))
    for i in range(28):
        for j in range(28):
            ds[i, j] = np.sum(array[i*mult:(i+1)*mult, j*mult:(j+1)*mult])/mult**2
    return ds


# +
fig, ax = plt.subplots(2, 3, sharex=True, sharey=True, constrained_layout=True)

a = X_test[119].reshape((28, 28)) / 255
a_scaled = skimage.transform.rescale(a, 7, order=0)

results = (
# downsample(a_scaled, 7)-a,
downsample(multiplex(a, 7), 7)-a,
downsample(multiplex_deterministic(a, 7), 7)-a,
downsample((a_scaled>blue[:196, :196])*1, 7)-a,
downsample(fill_fs(a_scaled), 7)-a,
downsample(fill_jjn(a_scaled), 7)-a)
results = np.array(results)

for i in range(len(results)):
    ax[i//3, i%3].imshow(results[i], cmap="Greys", vmin=np.amin(results), vmax=np.amax(results))
    ax[i//3, i%3].set_title(f"{np.mean(results[i]):.5f}\n{np.mean(np.abs(results[i])):.5f}\n{np.amax(results[i]):.5f}")

# ax[]
# -

diff = downsample(multiplex(a, 7), 7)-a
print(np.mean(diff), np.amax(np.abs(diff)))
print(1/255, 1/50)

# +
fig, ax = plt.subplots(5, 10, figsize=(20/2, 10/2))
ax = ax.flatten()

for i in range(25):
    a = X_test[i].reshape((28, 28))
    ax[i*2].imshow(a, cmap='Greys')
    ax[i*2].axis('off')
    
    ax[i*2+1].imshow(multiplex(a/255, 7), cmap='Greys')
    ax[i*2+1].axis('off')
# -

# # Do all?

from scipy.io import savemat

X_train, y_train = mnist_reader.load_mnist('data/fashion', kind='train')
X_test, y_test = mnist_reader.load_mnist('data/fashion', kind='t10k')

mult = 7
for dataset, name in ((X_train, f'X_train_{mult}.mat'), (X_test, f'X_test_{mult}.mat')):
    N = len(dataset)
    expanded = np.zeros((N, 28*mult, 28*mult), dtype=bool)
    images = dataset.reshape((N, 28, 28))/255
    
    for i in tqdm(range(N)):
        expanded[i,:,:] = multiplex(images[i], mult)
        
    savemat(name, {'data': expanded.astype(bool)}, do_compression=True)

expanded = np.zeros((10000, 28*7, 28*7))
X_test_images = X_test.reshape((10000, 28, 28))/255

# %%snakeviz
for i in tqdm(range(1000)):
    expanded[i,:,:] = multiplex(X_test_images[i], 7)

savemat("X_test_x7", {'data': expanded.astype(bool)}, do_compression=True)





expanded = np.zeros((10000, 28*7, 28*7))
X_test_images = X_test.reshape((10000, 28, 28))/255
