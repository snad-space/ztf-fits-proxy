import asyncio
import logging
from itertools import chain, count

import httpx
from astropy.coordinates import SkyCoord
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, create_model

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
            zip(count(1), FILTERS),  # 1 -> zg
        ]
    )
}


HMJD_QUERY = Query(title="Heliocentric modified Julian date of middle exposure", ge=58000)
RA_QUERY = Query(title="Right ascension in degrees", ge=0.0, lt=360.0)
DEC_QUERY = Query(title="Declination in degrees", ge=-90.0, le=90.0)
FIELDID_QUERY = Query(title="ZTF field ID", ge=1)
FILTER_QUERY = Query(title=f"ZTF filter name or ID, one of: {FILTERS}", ge=1, le=len(FILTERS), regex="z?[gri]")
RCID_QUERY = Query(title="ZTF read-out ID, equals to 4 x (CCDID - 1) + (QID - 1)", ge=0, lt=64)
OID_QUERY = Query(title="ZTF object ID", gt=0)
DR_QUERY = Query(default="latest", title="ZTF data release", regex="latest|dr[0-9]+")


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
    filter: str | int = FILTER_QUERY,
    fieldid: int = FIELDID_QUERY,
    rcid: int = RCID_QUERY,
) -> RegionExposure:
    """Get URLs for ZTF images by heliocentric modified Julian date, RA, Dec, filter, field ID and read-out ID."""
    filter = FILTER_MAP[filter]
    inputs = Inputs(hmjd=hmjd, ra=ra, dec=dec, filter=filter, fieldid=fieldid, rcid=rcid)

    ccdid = rcid // 4 + 1
    qid = rcid % 4 + 1

    coord = SkyCoord(ra=ra, dec=dec, unit="deg")
    date = DateWithFrac.from_hmjd(hmjd, coord)
    try:
        date = await date.correct()
    except httpx.HTTPError as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail="Failed to correct date")
    basename = date.basename(fieldid=fieldid, filter=filter, ccdid=ccdid, qid=qid)

    urls = URLs(**{ftype: f"{basename}_{fsuffix}" for ftype, fsuffix in FILE_TYPES.items()})

    return RegionExposure(inputs=inputs, urls=urls)


@router.get("/api/v1/urls/by/hmjd-oid", name="Get URLs by time and object ID")
async def urls_by_hmjd_oid(
    *,
    hmjd: float = HMJD_QUERY,
    oid: int = OID_QUERY,
    dr: str = DR_QUERY,
) -> RegionExposure:
    data = await get_by_oid(oid=oid, dr=dr)
    meta = data["meta"]
    coord = meta["coord"]
    return await urls_by_hmjd_ra_dec_rcid(
        hmjd=hmjd, ra=coord["ra"], dec=coord["dec"], filter=meta["filter"], fieldid=meta["fieldid"], rcid=meta["rcid"]
    )


@router.get("/api/v1/sciimg/by/oid", name="Redirect to sciimg file", status_code=307)
async def sciimg_by_oid(*, hmjd: float = HMJD_QUERY, oid: int = OID_QUERY, dr: str = DR_QUERY) -> RedirectResponse:
    region_exposure = await urls_by_hmjd_oid(hmjd=hmjd, oid=oid, dr=dr)
    return RedirectResponse(region_exposure.urls.sciimg)


@router.get("/api/v1/urls/by/oid", name="Get URLs for all exposures by object ID")
async def urls_by_oid(
    *,
    oid: int = OID_QUERY,
    dr: str = DR_QUERY,
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
        )
        for hmjd in hmjd_
    ]
    return await asyncio.gather(*tasks)
