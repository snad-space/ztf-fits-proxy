from importlib import metadata

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
def homepage() -> HTMLResponse:
    return HTMLResponse(content=f"""
<p>
    Welcome to <a href="SNAD">SNAD</a> API server for the ZTF FITS files look-ups.
</p>
<p>
    API v1 documentation is available at <a href="/api/docs"><font face="monospace">/api/redoc</font></a>.
</p>
<p>
    See source code as a part of <a href="{metadata.metadata("ztf-fits-url-finder")["Repository"]}"><font face="monospace">ztf-fits-proxy</font></a> project on GitHub.
</p>
""")  # noqa: E501
