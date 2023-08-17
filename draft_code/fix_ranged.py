# The problem is that I misdefined the fit ranges,
# not accounting for the blueshift thing. Blueshift
# is defined in terms of wavelength, whereas I store
# indices here, so this isn't trivial to fix actually

#%%
import sqlite3
import numpy as np
from io import BytesIO

#%%
dbconn = sqlite3.connect('test.db')
dbconn.row_factory = sqlite3.Row
# %%
for row in dbconn.execute("SELECT * FROM SuperPeakfinder"):
    if not row["skip"]:
        blueshift = row["fit_range_blueshift"]
        arrays = np.load(BytesIO(row["arrays"]))
        power = arrays[0]
        delta_p = power[-1] - power[0]
        positions = np.array((row["fit_range_left_b"], row["fit_range_right_a"]))
        positions += delta_p*blueshift
        print(positions)
# %%
