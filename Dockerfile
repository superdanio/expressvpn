FROM debian:bookworm-slim

LABEL maintainer="superdanio@gmail.com"

ENV ACTIVATION_CODE=Code
ENV LOCATION=smart
ENV PREFERRED_PROTOCOL=auto
ENV LIGHTWAY_CIPHER=auto

ARG APP_VERSION=3.76.0.4-1

RUN apt-get update && apt-get install -y --no-install-recommends \
    expect iproute2 curl iptables python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL "https://www.expressvpn.works/clients/linux/expressvpn_${APP_VERSION}_amd64.deb" -o /tmp/client.deb \
    && dpkg -i /tmp/client.deb \
    && rm /tmp/client.deb \
    && mkdir /vpn_shared

COPY docker/ /expressvpn
COPY app /app
COPY requirements.prod.txt /app
WORKDIR /app
RUN python3 -m venv .venv \
    && . .venv/bin/activate \
    && pip install -r requirements.prod.txt \
    && chmod a+x /expressvpn/*.sh


HEALTHCHECK --start-period=15s --interval=30s --timeout=5s CMD /expressvpn/healthcheck.sh

ENTRYPOINT ["/bin/bash", "/expressvpn/entrypoint.sh"]

EXPOSE 5000
