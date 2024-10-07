import os
from collections import defaultdict


ZTF_DR_DB_API_BASE_URL = os.environ.get("ZTF_DR_DB_API_BASE_URL", "https://db.ztf.snad.space")
ZTF_FITS_PRODUCTS_URL = os.environ.get("FITS_PRODUCTS_URL", "https://fits.ztf.snad.space/products/sci")

ZTF_FITS_PRODUCTS_BASE_URL_MAPPING = defaultdict(
    lambda: ZTF_FITS_PRODUCTS_URL,
    {
        "SNAD": "https://fits.ztf.snad.space/products/sci",
        "IPAC": "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/sci",
    },
)
