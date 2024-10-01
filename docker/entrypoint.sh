#!/usr/bin/env bash

cp /etc/resolv.conf /tmp/resolv.conf
umount /etc/resolv.conf
mv /tmp/resolv.conf /etc/resolv.conf
sed -i 's/DAEMON_ARGS=.*/DAEMON_ARGS=""/' /etc/init.d/expressvpn
service expressvpn restart
/usr/bin/expect /expressvpn/activate.sh
expressvpn preferences set auto_connect true
expressvpn preferences set preferred_protocol $PREFERRED_PROTOCOL
expressvpn preferences set lightway_cipher $LIGHTWAY_CIPHER

if [[ "$CONNECT_AT_STARTUP" == "true" ]]; then
  expressvpn connect $SERVER
fi

if [[ "$(expressvpn status)" == "Not Activated" ]]; then exit 1; fi

cp /etc/resolv.conf /vpn_shared/resolv.conf

source .venv/bin/activate
cd /app
flask run --host=0.0.0.0
