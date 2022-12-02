FROM rust:bullseye AS builder

ENV VERSION=0.1.4
RUN cargo install geo302 --version=${VERSION} --root=/


FROM debian:bullseye-slim

RUN apt-get update \
    && apt-get install -y ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app
COPY GeoLite2-Country.mmdb /app/geolite2.mmdb
COPY geo302.toml /app/geo302.toml
COPY --from=builder /bin/geo302 /app/geo302

CMD ["./geo302", "./geo302.toml"]
