# ZTF FITS images finder by heliocentric MJD from data releases

This is a simple tool to find ZTF FITS images by heliocentric MJD from data releases.
If you know the heliocentric MJD of an observation and data release (DR) object identifier (OID), you can use `/api/v1/urls/by/hmjd-oid`.
If you need to get URLs for the whole light curve of an object, you can use `/api/v1/urls/by/oid`, which is quite slow.
An example of the call with Python [`requests`](https://requests.readthedocs.io/en/master/) library is given below.

```python
from pprint import pprint

import matplotlib.pyplot as plt
import requests
from astropy.io import fits


url = "https://finder.fits.ztf.snad.space/api/v1/urls/by/oid"
params = {"oid": 633207400004730, "dr": "latest"}
with requests.get(url, params=params) as r:
    r.raise_for_status()
    data = r.json()

# Print the whole response
pprint(data)

# Extract scientific image URLs:
urls = [obs["urls"]["sciimg"] for obs in data]
print(urls)

# Download and show the first image
hdus = fits.open(urls[0])
plt.imshow(hdus[1].data, origin="lower")
```
