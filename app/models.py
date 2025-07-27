from dataclasses import dataclass, field
from typing import Literal, TypedDict

@dataclass
class Version:
    version: str

class SinglePreference(TypedDict):
    key: str
    value: str | list[str]

@dataclass
class IPs:
    vpn_ip: str
    public_ip: str

Protocol = Literal['auto', 'lightwayudp', 'lightwaytcp', 'openvpnudp', 'openvpntcp']
ConnectionState = Literal[
        'Disconnected',
        'Connecting',
        'Connected',
        'Interrupted',
        'Reconnecting',
        'DisconnectingToReconnect',
        'Disconnecting',
        'Failed']

Preferences = TypedDict(
        'Preferences',
        {
            'allowlan': bool,
            'autoconnect': bool,
            'blockAds': bool,
            'blockAdult': bool,
            'blockAll': bool,
            'blockMalicious': bool,
            'blockTrackers': bool,
            'debuglogging': str,
            'dnsconfigured': bool,
            'networklock': str,
            'protocol': Protocol,
            'split-app': list[str],
            'splittunnel': bool,
            })

@dataclass
class StatusResponse:
    status: ConnectionState
    server: str | None = None

@dataclass
class ServerList:
    servers: dict[str, list[str]] = field(default_factory=dict)

@dataclass
class Configuration:
    preferences: dict[str, str] = field(default_factory=dict)
