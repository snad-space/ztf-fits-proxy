from importlib import metadata

from fastapi import FastAPI


from . import root, v1
from .http_client import http_client

app = FastAPI(
    title="ZTF FITS Finder API by SNAD",
    version=metadata.version("ztf-fits-url-finder"),
    contact=dict(
        name=metadata.metadata("ztf-fits-url-finder")["Author"],
        email=metadata.metadata("ztf-fits-url-finder")["Author-email"],
        url=metadata.metadata("ztf-fits-url-finder")["Repository"],
    ),
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url="/api/docs",
)
app.include_router(root.router)
app.include_router(v1.router)


@app.on_event("startup")
async def startup_event():
    http_client.start()


@app.on_event("shutdown")
async def shutdown_event():
    await http_client.stop()
