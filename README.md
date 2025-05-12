# A collection of services for ZTF FITS image access and discover

The original purpose of this project was to bypass CORS restrictions on the ZTF FITS image access for [JS9](https://js9.si.edu/js9/) widget used by [SNAD Viewer](https://ztf.snad.space/).

## Services

### Caching proxy of IRSA IPAC ZTF FITS archive

This service is an Nginx caching proxy for https://irsa.ipac.caltech.edu/ibe/data/ztf/products.
It is represented by two Docker containers: one for the Nginx proxy itself  (see `proxy` folder) and another one is for filling the directory tree cache on the service startup (see `proxy-cache-filler`).
Currently, the service is deployed to two locations: http://sai.fits.ztf.snad.space and http://uci.fits.ztf.snad.space, see `docker-compose-sai.yml` and `docker-compose-uci.yml` for details.
However, the end user should use a redirect proxy to access the service.

### FITS finder API

The service is an API that returns a list of ZTF photometry products for a given observation of a ZTF DR object.
See `fits-finder/README.md` for details.
It is deployed to http://finder.fits.ztf.snad.space, see `docker-compose-finder.yml`.
