import re
from dataclasses import dataclass

import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time

from .config import ZTF_FITS_PRODUCTS_URL
from .http_client import http_client


PALOMAR = EarthLocation(lon=-116.863, lat=33.356, height=1706)  # EarthLocation.of_site('Palomar')


def hmjd_to_earth(hmjd: float, coord: SkyCoord):
    t = Time(hmjd, format="mjd")
    return t - t.light_travel_time(coord, kind="heliocentric", location=PALOMAR)


@dataclass
class DateWithFrac:
    year: int
    month: int
    day: int
    fraction: float
    frac_decimal_digits: int = 6

    @classmethod
    def from_hmjd(cls, *, hmjd: float, coord: SkyCoord) -> "DateWithFrac":
        t = hmjd_to_earth(hmjd, coord)
        dt = t.to_datetime()
        return cls(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            fraction=t.mjd % 1,
        )

    @property
    def monthday(self) -> str:
        return f"{self.month:02d}{self.day:02d}"

    def frac_digits(self, digits: int = 6) -> int:
        return int(round(self.fraction * 10**digits))

    def repr(self, digits: int = frac_decimal_digits) -> str:
        return f"{self.year}{self.monthday}{self.frac_digits(digits):0{digits}d}"

    def folder_day(self, base_url: str) -> str:
        return f"{base_url}/{self.year}/{self.monthday}/"

    def folder(self, base_url: str) -> str:
        return f"{base_url}/{self.year}/{self.monthday}/{self.frac_digits():06d}/"

    def basename(self, *, fieldid: int, filter: str, ccdid: int, qid: int, base_url: str) -> str:
        return f"{self.folder(base_url)}ztf_{self.repr()}_{fieldid:06d}_{filter}_c{ccdid:02d}_o_q{qid}"

    def path(
        self, *, suffix: str = "sciimg.fits", fieldid: int, filter: str, ccdid: int, qid: int, base_url: str
    ) -> str:
        return f"{self.basename(fieldid=fieldid, filter=filter, ccdid=ccdid, qid=qid, base_url=base_url)}_{suffix}"

    async def fracs_in_day_folder(self) -> list[int]:
        response = await http_client.get(self.folder_day(base_url=ZTF_FITS_PRODUCTS_URL), follow_redirects=True)
        response.raise_for_status()
        body = response.text
        fracs = re.findall(r'<a href="(\d{6})/">\1/</a>', body)
        return sorted(int(f) for f in fracs)

    async def correct(self) -> "DateWithFrac":
        fracs = await self.fracs_in_day_folder()
        i = np.searchsorted(fracs, self.frac_digits(self.frac_decimal_digits))
        self.fraction = fracs[i - 1] / (10.0**self.frac_decimal_digits)
        return self
