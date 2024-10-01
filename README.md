# ExpressVPN in a container
Taking inspiration from the work done here: https://github.com/polkaned/dockerfiles/tree/master/expressvpn

This image allows you to have more control of your VPN connection, exposing a very simple API and minimalistic UI to interact with _expressvpn_ client.

Other containers can use the network of the expressvpn container by declaring the entry `network_mode: service:expressvpn` and mounting a volume to replace /etc/resolv.conf.

All traffic from the container will be routed via the vpn container. To reach the other containers locally the port forwarding must be done in the vpn container (the network mode service does not allow a port configuration).

## Prerequisites

1. Get your activation code from ExpressVPN web site.

## API

| Method   | Endpoint                                            | Description                                                 |
|----------|-----------------------------------------------------|-------------------------------------------------------------|
| **GET**  | _/api/preferences_                                  | Returns the preferences currently in use                    |
| **GET**  | _/api/servers_                                      | Returns the list of servers you can connect to              |
| **GET**  | _/api/status_                                       | Returns the current status of the connection                |
| **GET**  | _/api/test?url=\<string\>_                          | Redirects to the given url. Useful for testing connectivity |
| **GET**  | _/api/version                                       | Returns the expressvpn client version                       |
| **POST** | _/api/connect/\<string:server\>_                    | Connects to the given server or to 'smart' if blank         |
| **POST** | _/api/disconnect_                                   | Disconnects from current server                             |
| **POST** | _/api/preferences/\<string:name\>/\<string:value\>_ | Sets the given preference                                   |
| **POST** | _/api/refresh_                                      | Refreshes the current VPN cluster                           |

## UI
A very minimalistic UI is exposed on the main port. Nothing fancy, just plain html and javascript to keep it simple.

## Docker Compose

```
services:

  expressvpn:
    container_name: expressvpn
    image: superdanio/expressvpn
    environment:
      - ACTIVATION_CODE={% your-activation-code %}
      - SERVER={% LOCATION/ALIAS/COUNTRY %}
      - PREFERRED_PROTOCOL={% protocol %}
      - LIGHTWAY_CIPHER={% lightway-cipher %}
      - CONNECT_AT_STARTUP={% true | false %}
      - HEALTHCHECK_TARGET={% url %}
    cap_add:
      - NET_ADMIN
    devices: 
      - /dev/net/tun
    stdin_open: true
    tty: true
    privileged: true
    restart: unless-stopped
    volumes:
      - /tmp/vpn:/vpn_shared
    ports:
      - "5000:5000" # exposing API port
      # ports of other containers that use the vpn (to access them locally)
  
  curl:
    image: alpine/curl
    container_name: curl
    command: sleep infinity
    network_mode: service:expressvpn
    depends_on:
      expressvpn:
        condition: service_healthy
    volumes:
      - /tmp/vpn/resolv.conf:/etc/resolv.conf
  ```

You can test it by executing:

```
docker compose exec -it curl curl ifconfig.me
```

## Configuration Reference

### ACTIVATION\_CODE
A mandatory string containing your ExpressVPN activation code.

`ACTIVATION_CODE=ABCD1EFGH2IJKL3MNOP4QRS`

### SERVER
An optional string containing the ExpressVPN server LOCATION/ALIAS/COUNTRY. Connect to smart location if it is not set.

`SERVER=ukbe`

### PREFERRED\_PROTOCOL
An optional string containing the ExpressVPN protocol. Can be auto, udp, tcp ,lightway_udp, lightway_tcp. Use auto if it is not set.

`PREFERRED_PROTOCOL=lightway_udp`

### LIGHTWAY\_CIPHER
An optional string containing the ExpressVPN lightway cipher. Can be auto, aes, chacha20. Use auto if it is not set.

`LIGHTWAY_CIPHER=chacha20`

### CONNECT\_AT\_STARTUP
An optional string (representing a boolean) to determine whether it should connect to a server at startup.

### HEALTHCHECK\_TARGET
An optional string representing the url to hit for healthcheck. Default: http://ifconfig.me
If the schema is not provided, the url will be resolved as internal to the api: i.e. `status` => `http://localhost:5000/api/status`

## Local environment
### Setup
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Build
```
docker build -t expressvpn:local .
```

### Tests
```
ACTIVATION_CODE=YOUR_CODE TARGET_IMAGE=expressvpn:local pytest -v tests/
```

### Run
```
docker run -it --privileged --cap-add=NET_ADMIN --device=/dev/net/tun -p 25000:5000 -e ACTIVATION_CODE=<YOUR_CODE> -e CONNECT_AT_STARTUP=true expressvpn:local
```

