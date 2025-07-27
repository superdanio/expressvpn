FROM debian:bookworm-slim
LABEL maintainer="superdanio@gmail.com"

ENV ACTIVATION_CODE=Code
ENV LOCATION=smart
ENV PREFERRED_PROTOCOL=auto
ENV LIGHTWAY_CIPHER=auto

ARG TARGETARCH
ARG APP_VERSION=4.0.1.9292

RUN if [ "$TARGETARCH" = arm64 ]; then dpkg --add-architecture armhf; fi; \
    apt-get update && \
    if [ -z "${TARGETARCH%%arm*}" ]; then apt-get install -y --no-install-recommends libc6:armhf; fi; \
    apt-get install -y --no-install-recommends --no-install-suggests expect iproute2 curl iptables python3-venv procps sudo systemd libglib2.0-0 libxkbcommon-x11-0 libnl-3-200 libnl-route-3-200 psmisc libatomic1 libopengl0 xterm gcc \
    && rm -rf /var/lib/apt/lists/*; \
    useradd -m vpn && \
    echo "vpn ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/vpn && \
    if [ "$TARGETARCH" = arm64 ]; then ln -s $(find /lib -name 'ld-*.so' | grep 'arm-linux-gnueabihf' | head -n 1) ld-linux.so.3; fi; \
    curl -sL "https://www.expressvpn.works/clients/linux/expressvpn-linux-universal-${APP_VERSION}.run" -o /tmp/client.run \
    && chmod a+x /tmp/client.run \
    && chown vpn:vpn /tmp/client.run


ENV LD_LIBRARY_PATH=/opt/expressvpn/lib

USER vpn


COPY --chown=vpn:vpn docker/ /home/vpn/expressvpn
COPY --chown=vpn:vpn app /home/vpn/app
COPY --chown=vpn:vpn requirements.prod.txt /home/vpn/app

RUN /home/vpn/expressvpn/install.sh

WORKDIR /home/vpn/app
 RUN mkdir /home/vpn/vpn_shared \
     && python3 -m venv .venv \
     && . .venv/bin/activate \
     && pip install -r requirements.prod.txt \
     && chmod a+x /home/vpn/expressvpn/*.sh


HEALTHCHECK --start-period=15s --interval=30s --timeout=5s CMD /hpme/vpn/expressvpn/healthcheck.sh

ENTRYPOINT ["/bin/bash", "/home/vpn/expressvpn/entrypoint.sh"]

EXPOSE 5000
