FROM debian:bookworm-slim
LABEL maintainer="superdanio@gmail.com"

ENV ACTIVATION_CODE=Code
ENV LOCATION=smart
ENV PREFERRED_PROTOCOL=auto
ENV LIGHTWAY_CIPHER=auto

ARG TARGETARCH
ARG APP_VERSION=3.76.0.4-1

RUN if [ "$TARGETARCH" = arm64 ]; then dpkg --add-architecture armhf; fi; \
    apt-get update && \
    if [ -z "${TARGETARCH%%arm*}" ]; then apt-get install -y --no-install-recommends libc6:armhf; fi; \
    apt-get install -y --no-install-recommends expect iproute2 curl iptables python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sL "https://www.expressvpn.works/clients/linux/expressvpn_${APP_VERSION}_$([ $TARGETARCH = amd64 ] && echo amd64 || echo armhf).deb" -o /tmp/client.deb \
    && dpkg -i /tmp/client.deb \
    && rm /tmp/client.deb

COPY docker/ /expressvpn
COPY app /app
COPY requirements.prod.txt /app
WORKDIR /app
RUN mkdir /vpn_shared \
    && python3 -m venv .venv \
    && . .venv/bin/activate \
    && pip install -r requirements.prod.txt \
    && chmod a+x /expressvpn/*.sh


HEALTHCHECK --start-period=15s --interval=30s --timeout=5s CMD /expressvpn/healthcheck.sh

ENTRYPOINT ["/bin/bash", "/expressvpn/entrypoint.sh"]

EXPOSE 5000
