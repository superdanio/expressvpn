from dataclasses import dataclass, field
from enum import Enum

@dataclass
class Version:
    version: str

class Status(str, Enum):
    DISCONNECTED = 'DISCONNECTED'
    CONNECTED = 'CONNECTED'
    UNABLE_TO_CONNECT = 'UNABLE_TO_CONNECT'
    FAILED = 'FAILED'

@dataclass
class StatusResponse:
    status: Status
    server: str | None = None

@dataclass
class ServerDetails:
    alias: str
    location: str
    recommended: bool

@dataclass
class ServerList:
    servers: dict[str, list[ServerDetails]] = field(default_factory=dict)

@dataclass
class Configuration:
    preferences: dict[str, str] = field(default_factory=dict)
