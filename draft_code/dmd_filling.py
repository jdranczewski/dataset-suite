import numpy as np
from scipy.signal import convolve
# %matplotlib widget
import matplotlib.pyplot as plt
from ipywidgets import interact
from tqdm.autonotebook import tqdm
from skimage.io import imread

# +
fig, ax = plt.subplots()

def fill(Nx, Ny, filling):
    arr = np.zeros((Ny, Nx))
    for i in range(Ny):
        for j in range(Nx):
            if np.sum(arr)/(i*Nx+j+1) < filling:
                arr[i,j] = 1
    return arr

@interact(Nx=(1,40,1), Ny=(1,40,1))
def update(Nx=20, Ny=20, filling=0.25):
    arr = fill(Nx, Ny, filling)
    im.set_data(arr)
    print(np.sum(arr)/arr.size)

im = ax.imshow(fill(20, 20, 0.25))


# -

# # Hilbert curve

# +
# Algorithm from Wikipedia
def rot(n, x, y, rx, ry):
    if (ry == 0):
        if (rx == 1):
            x = n-1 - x;
            y = n-1 - y;

        x, y = y, x
    return x, y

def d2xy(n, d):
    t=d
    x = y = 0
    s = 1
    while s<n:
        rx = 1 & (t//2);
        ry = 1 & (t ^ rx);
        x, y = rot(s, x, y, rx, ry);
        x += s * rx;
        y += s * ry;
        t //= 4;
        s*=2
    return x, y


# -

fig, ax = plt.subplots()
hilbert = np.array([d2xy(32*32,i) for i in range(32*32)])
ax.plot(hilbert[:,0], hilbert[:,1], "x-")

# +
fig, ax = plt.subplots()

def fill_hilbert(filling):
    arr = np.zeros((32, 32))
    for i, coord in enumerate(hilbert):
        #print(np.sum(arr), coord)
        if np.sum(arr)/(i+1) < filling:
            arr[coord[0], coord[1]] = 1
    return arr

@interact(filling=(0,1,0.001))
def update_hilbert(filling=0.251):
    arr = fill_hilbert(filling)
    im.set_data(arr)
    print(np.sum(arr)/arr.size)

im = ax.imshow(fill_hilbert(0.1))
ax.plot(hilbert[:,0], hilbert[:,1], "-")
# -

# # 'Floyd - Steinberg' and 'Minimized average error dithering' by Jarvis, Judice, and Ninke

# +
N=32

def fill_fs(filling):
    arr = np.zeros((N+2,N+2)) + filling
    for y in range(1,N+1):
        for x in range(1,N+1):
            old = arr[x,y]
            new = np.round(old)
            arr[x,y] = new
            quant_error = old - new
            arr[x-1:x+2, y:y+2] += quant_error/16 * np.array([[0, 0, 7],[3, 5, 1]]).T
    return arr[1:-1, 1:-1]

def fill_jjn(filling):
    arr = np.zeros((N+4,N+4)) + filling
    for y in range(2,N+2):
        for x in range(2,N+2):
            old = arr[x,y]
            new = np.round(old)
            arr[x,y] = new
            quant_error = old - new
            arr[x-2:x+3, y:y+3] += quant_error/48 * np.array([[0, 0, 0, 7, 5],[3, 5, 7, 5, 3], [1, 3, 5, 3, 1]]).T
    return arr[2:-2, 2:-2]

def fill_rand(filling):
    return (np.random.random((N,N))<filling)*1
            
@interact(method=[fill_fs, fill_jjn, fill_rand, fill_hilbert], filling=(0,1,0.001))
def update_fs(method=fill_jjn, filling=0.251):
    arr = method(filling)
    conv = convolve(arr, np.ones((11,11)), 'valid')/100/filling
    im.set_data(arr)
    im2.set_data(conv)
    print(arr.shape)
    print(filling, np.sum(arr)/arr.size)
    print(np.std(conv))
    
fig, ax = plt.subplots(1,2)
im = ax[0].imshow(fill_fs(0.1))
im2 = ax[1].imshow(convolve(fill_fs(0.1), np.ones((10,10)), 'valid')/100/0.1)
# -

# # Correcting randomness

N=32
filling = np.pi/10
arr = (np.random.random((N,N))<filling)*1
conv = convolve(arr, np.ones((11,11)), 'valid')/100/filling
arr

done = 0
for i in tqdm(range(10)):
    if np.mean(arr[5:-5,5:-5])>filling:
        print("Remove")
        pos_args = np.argwhere(arr[5:-5,5:-5])
        conv = convolve(arr, np.ones((11,11)), 'valid')/100/filling
        for i in range(1000):
            pos_i = np.random.randint(len(pos_args))
            pos_prob = (conv[pos_args[pos_i][0], pos_args[pos_i][1]]-1)/(np.amax(conv)-1)
            if pos_prob>np.random.random():
                done += 1
                arr[pos_args[pos_i][0]+5, pos_args[pos_i][1]+5] = 0
                break
    
    if np.mean(arr[5:-5,5:-5])<filling:
        print("Add")
        pos_args = np.argwhere(arr[5:-5,5:-5]==0)
        conv = convolve(arr, np.ones((11,11)), 'valid')/100/filling
        for i in range(10):
            pos_i = np.random.randint(len(pos_args))
            pos_prob = (1-conv[pos_args[pos_i][0], pos_args[pos_i][1]])/(1-np.amin(conv))
            print(conv[pos_args[pos_i][0], pos_args[pos_i][1]])
            print(arr[pos_args[pos_i][0]+5, pos_args[pos_i][1]+5])
            if pos_prob>np.random.random():
                done += 1
#                 print(arr[pos_args[pos_i][0]+5, pos_args[pos_i][1]+5])
                arr[pos_args[pos_i][0]+5, pos_args[pos_i][1]+5] = 1
#                 print(arr[pos_args[pos_i][0]+5, pos_args[pos_i][1]+5])
                break
#     conv = convolve(arr, np.ones((11,11)), 'valid')/100/filling
#     print(np.std(conv))

fig, ax = plt.subplots(1,2)
im = ax[0].imshow(arr)
im2 = ax[1].imshow(convolve(arr, np.ones((11,11)), 'valid')/100/filling)pos_prob

fig, ax = plt.subplots(1,2)
im = ax[0].imshow(arr)
im2 = ax[1].imshow(convolve(arr, np.ones((11,11)), 'valid')/100/filling)

fig, ax = plt.subplots(1,2)
im = ax[0].imshow(arr)
im2 = ax[1].imshow(convolve(arr, np.ones((11,11)), 'valid')/100/filling)

# # Bias

x, y = np.meshgrid(np.linspace(-1,1,21), np.linspace(-1,1,21))
d = np.sqrt(x*x+y*y)
sigma, mu = 1.0, 0.0
kernel= np.exp(-( (d-mu)**2 / ( 2.0 * sigma**2 ) ) )
fig, ax = plt.subplots()
ax.imshow(kernel)

N=100
filling = 0.1
rnd = np.random.random((N,N))
arr = (rnd<filling)*1
conv = convolve(arr, kernel, 'valid')/21**2/filling - 1
arr

fig, ax = plt.subplots(1,3, sharex=True, sharey=True)
ax[0].imshow(rnd)
ax[1].imshow(arr)
ax[2].imshow(conv, extent=(10.5, 100-10.5, 10.5, 100-10.5))

conv = convolve(arr, kernel, 'valid')/11**2/filling - 1
std = []
for i in range(1000):
    rnd[10:-10,10:-10] += conv*0.001*np.random.random((N-20,N-20))
    arr = (rnd<filling)*1
    conv = convolve(arr, kernel, 'valid')/21**2/filling - 1
    std.append(np.std(conv))
fig, ax = plt.subplots()
ax.plot(std)

fig, ax = plt.subplots(1,3, sharex=True, sharey=True)
ax[0].imshow(rnd)
ax[1].imshow(arr)
ax[2].imshow(conv, extent=(10.5, 100-10.5, 10.5, 100-10.5))

# # Generate with bias

# +
arr = np.zeros((64,64))
filling=0.1

for i in range(1000):
    # State before
    pos = np.random.randint(0,64-20,2)
    conv_prev = np.abs(1-(convolve(arr, np.ones((21,21)), 'valid')/21**2/filling)[pos[0], pos[1]])
    
    # Do it
    arr[pos[0]+10, pos[1]+10] = 1
    conv_after = np.abs(1-(convolve(arr, np.ones((21,21)), 'valid')/21**2/filling)[pos[0], pos[1]])
    
    # If convolution worsened, reject change
    if conv_after > conv_prev:
        arr[pos[0]+10, pos[1]+10] = 0
# -

fig, ax = plt.subplots(1,2)
ax[0].imshow(arr)
ax[1].imshow(1-(convolve(arr, np.ones((21,21)), 'valid')/21**2/filling))

# # Heck it, springs

N = 50
# positions = np.random.randint(0,32,(N,2)).astype(float)
positions = np.vstack((np.stack((np.arange(0,N)%32, np.arange(0,N)//32)).T,
                       np.stack((np.arange(-1,33,1), np.zeros(34)-1)).T,
                       np.stack((np.zeros(33)-1, np.arange(0,33,1))).T,
                       np.stack((np.arange(0,33,1), np.zeros(33)+32)).T,
                       np.stack((np.zeros(32)+32, np.arange(0,32,1))).T))

fig, ax = plt.subplots()
l, = ax.plot(positions[:,0], positions[:,1], "x")

for j in range(500):
#     sleep(0.01)
    for i in range(N):
        dist = np.vstack((positions[:i], positions[i+1:])) - positions[i]
#         d = np.sqrt(np.sum(dist**2, axis=1)).reshape((-1,1))
#         forces = (5/(d-0.6) + 50/(-d**2-6)) * dist/d
        forces = dist/np.sum(dist**2, axis=1).reshape((-1,1))**(1/2)
        force = ((np.sum(forces, axis=0)))*j/500
        positions[i,:] -= force
        positions[:N][positions[:N]<0] = 0
        positions[:N][positions[:N]>32] = 32
    l.set_data(positions[:,0], positions[:,1])
    fig.canvas.draw()

# # Gradient descent

filling = 0.122
arr = (np.random.random((64, 64)) < filling)*1

con = convolve(arr, np.ones((21,21)), 'valid')/21**2/filling
pos = np.argwhere(arr[11:-11, 11:-11])+1
gradient_x = con[1:,:]-con[:-1,:]

fig, ax = plt.subplots(1,2)
ax[0].imshow(con)
ax[1].imshow(gradient_x)

# # Blue noise



# # Take it in small units

def three(N):
    filled = []
    for i in range(N):
        j = np.random.randint(0, 9-len(filled))
        filled.append([x for x in range(9) if x not in filled][j])
    return np.array([1 if x in filled else 0 for x in range(9)]).reshape((3,3))


arr = np.zeros((30,30))
for i in range(10):
    for j in range(10):
        arr[i*3:(i+1)*3, j*3:(j+1)*3] = three(2)

fig, ax = plt.subplots()
ax.imshow(arr)

# # Blue noise

blue = imread("HDR_L_0.png")/(2**16-1)

np.mean(blue < 0.314)

fig, ax = plt.subplots(1,2, sharex=True, sharey=True)
ax[0].imshow(blue<0.4)
ax[1].imshow(convolve(blue<0.4, np.ones((21,21)), 'valid')/21**2/0.4-1)

# ## Try a low res version

b_small = blue[123:123+32, 24:24+32]

np.mean(b_small < 0.314)

fig, ax = plt.subplots(1,2, sharex=True, sharey=True)
ax[0].imshow(b_small<0.4)
ax[1].imshow(convolve(b_small<0.4, np.ones((21,21)), 'valid')/21**2/0.4-1)
print(np.std(convolve(b_small<0.4, np.ones((21,21)), 'valid')/21**2/0.4))


