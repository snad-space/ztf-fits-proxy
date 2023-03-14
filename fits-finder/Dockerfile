FROM python:3.10-slim

EXPOSE 80

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost//api/v1/urls/by/hmjd-ra-dec-rcid?hmjd=58198.45875&ra=247.45543&dec=24.77282&filter=zr&fieldid=633&rcid=27 || exit 1

RUN pip3 install gunicorn 'uvicorn[standard]'

COPY pyproject.toml /app/pyproject.toml
COPY fits_finder /app/fits_finder

WORKDIR /app

RUN pip3 install .

ENTRYPOINT ["gunicorn", "-w4", "-b0.0.0.0:80", "--worker-class=uvicorn.workers.UvicornWorker", "--timeout", "60", "fits_finder.main:app"]
