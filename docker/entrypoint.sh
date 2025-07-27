#!/usr/bin/env bash

sudo cp /etc/resolv.conf /tmp/resolv.conf
sudo umount /etc/resolv.conf
sudo mv /tmp/resolv.conf /etc/resolv.conf

nohup sudo /opt/expressvpn/bin/expressvpn-daemon &
echo "$ACTIVATION_CODE" > $HOME/activation.code
expressvpnctl background enable
expressvpnctl login $HOME/activation.code
if [[ "$?" -ne 0 ]]; then exit 1; fi
expressvpnctl set protocol $PREFERRED_PROTOCOL
sudo expressvpnctl set split-app bypass:/home/vpn/app/.venv/bin/python3
sudo expressvpnctl set splittunnel true

if [[ "$CONNECT_AT_STARTUP" == "true" ]]; then
  expressvpnctl set autoconnect true
  expressvpnctl connect $SERVER
fi

expressvpnctl status
if [[ "$(expressvpnctl status)" == "Not Activated" ]]; then exit 1; fi

sudo cp /etc/resolv.conf $HOME/vpn_shared/resolv.conf

cd $HOME/app
source .venv/bin/activate
flask run --host=0.0.0.0
