import asyncio
import logging
from itertools import chain, count

import httpx
from astropy.coordinates import SkyCoord
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, create_model

from .config import ZTF_FITS_PRODUCTS_URL, ZTF_FITS_PRODUCTS_BASE_URL_MAPPING
from .date_with_frac import DateWithFrac
from .ztf_db import get_by_oid

router = APIRouter()

FILE_SUFFIXES = [
    "alerts.tar.gz",
    "diffimgpsf.fits",
    "diffimlog.txt",
    "log.txt",
    "mskimg.fits",
    "psfcat.fits",
    "sciimg.fits",
    "sciimgdao.psf",
    "sciimgdaopsfcent.fits",
    "sciimlog.txt",
    "scimrefdiffimg.fits.fz",
    "sexcat.fits",
]
FILE_TYPES = {fname.split(".")[0]: fname for fname in FILE_SUFFIXES}

FILTERS = ["zg", "zr", "zi"]
FILTER_MAP = {
    k: v
    for k, v in chain.from_iterable(
        [
            zip(FILTERS, FILTERS),  # zg -> zg
            zip([f[1] for f in FILTERS], FILTERS),  # g -> zg
            zip(map(str, count(1)), FILTERS),  # 1 -> zg
        ]
    )
}


HMJD_QUERY = Query(title="Heliocentric modified Julian date of middle exposure", ge=58000)
RA_QUERY = Query(title="Right ascension in degrees", ge=0.0, lt=360.0)
DEC_QUERY = Query(title="Declination in degrees", ge=-90.0, le=90.0)
FIELDID_QUERY = Query(title="ZTF field ID", ge=1)
FILTER_QUERY = Query(title=f"ZTF filter name or ID, one of: {FILTERS}", regex="z?[gri]|[123]")
RCID_QUERY = Query(title="ZTF read-out ID, equals to 4 x (CCDID - 1) + (QID - 1)", ge=0, lt=64)
OID_QUERY = Query(title="ZTF object ID", gt=0)
DR_QUERY = Query(default="latest", title="ZTF data release", regex="latest|dr[0-9]+")
BASE_URL_QUERY = Query(
    default=ZTF_FITS_PRODUCTS_URL,
    title=f"Base URL of scientific ZTF products, such as {ZTF_FITS_PRODUCTS_URL}, or one of of the code names: {list(ZTF_FITS_PRODUCTS_BASE_URL_MAPPING)}",  # noqa: E501
    regex=r"SNAD|IPAC|https?://\S+",
)


class Inputs(BaseModel):
    hmjd: float
    ra: float
    dec: float
    filter: str
    fieldid: int
    rcid: int


URLs = create_model("URLs", **{k: (str, ...) for k in FILE_TYPES})


class RegionExposure(BaseModel):
    inputs: Inputs
    urls: URLs


@router.get("/api/v1/urls/by/hmjd-ra-dec-rcid", name="Get URLs by time and position")
async def urls_by_hmjd_ra_dec_rcid(
    *,
    hmjd: float = HMJD_QUERY,
    ra: float = RA_QUERY,
    dec: float = DEC_QUERY,
    filter: str = FILTER_QUERY,
    fieldid: int = FIELDID_QUERY,
    rcid: int = RCID_QUERY,
    base_url: str = BASE_URL_QUERY,
) -> RegionExposure:
    """Get URLs for ZTF images by heliocentric modified Julian date, RA, Dec, filter, field ID and read-out ID."""
    filter = FILTER_MAP[filter]
    inputs = Inputs(hmjd=hmjd, ra=ra, dec=dec, filter=filter, fieldid=fieldid, rcid=rcid)

    ccdid = rcid // 4 + 1
    qid = rcid % 4 + 1

    base_url = ZTF_FITS_PRODUCTS_BASE_URL_MAPPING[base_url]

    coord = SkyCoord(ra=ra, dec=dec, unit="deg")
    date = DateWithFrac.from_hmjd(hmjd=hmjd, coord=coord)
    try:
        date = await date.correct()
    except httpx.HTTPError as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail="Failed to correct date")
    basename = date.basename(fieldid=fieldid, filter=filter, ccdid=ccdid, qid=qid, base_url=base_url)

    urls = URLs(**{ftype: f"{basename}_{fsuffix}" for ftype, fsuffix in FILE_TYPES.items()})

    return RegionExposure(inputs=inputs, urls=urls)


@router.get("/api/v1/urls/by/hmjd-oid", name="Get URLs by time and object ID")
async def urls_by_hmjd_oid(
    *,
    hmjd: float = HMJD_QUERY,
    oid: int = OID_QUERY,
    dr: str = DR_QUERY,
    base_url: str = BASE_URL_QUERY,
) -> RegionExposure:
    data = await get_by_oid(oid=oid, dr=dr)
    meta = data["meta"]
    coord = meta["coord"]
    return await urls_by_hmjd_ra_dec_rcid(
        hmjd=hmjd,
        ra=coord["ra"],
        dec=coord["dec"],
        filter=meta["filter"],
        fieldid=meta["fieldid"],
        rcid=meta["rcid"],
        base_url=base_url,
    )


@router.get("/api/v1/sciimg/by/hmjd-oid", name="Redirect to sciimg file", status_code=307)
async def sciimg_by_hmjd_oid(
    *, hmjd: float = HMJD_QUERY, oid: int = OID_QUERY, dr: str = DR_QUERY, base_url: str = BASE_URL_QUERY
) -> RedirectResponse:
    region_exposure = await urls_by_hmjd_oid(hmjd=hmjd, oid=oid, dr=dr, base_url=base_url)
    return RedirectResponse(region_exposure.urls.sciimg)


@router.get("/api/v1/urls/by/oid", name="Get URLs for all exposures by object ID")
async def urls_by_oid(
    *,
    oid: int = OID_QUERY,
    dr: str = DR_QUERY,
    base_url: str = BASE_URL_QUERY,
) -> list[RegionExposure]:
    data = await get_by_oid(oid=oid, dr=dr)
    hmjd_ = [obs["mjd"] for obs in data["lc"]]
    meta = data["meta"]
    coord = meta["coord"]
    tasks = [
        urls_by_hmjd_ra_dec_rcid(
            hmjd=hmjd,
            ra=coord["ra"],
            dec=coord["dec"],
            filter=meta["filter"],
            fieldid=meta["fieldid"],
            rcid=meta["rcid"],
            base_url=base_url,
        )
        for hmjd in hmjd_
    ]
    return await asyncio.gather(*tasks)
