import os
import re
import shutil
import subprocess
from typing import cast
from cachetools import cached, TTLCache

from models import ConnectionState, IPs, Preferences, ServerList, StatusResponse, Version

class Client:

    CMD = 'expressvpnctl'
    ANSI_ESCAPE = re.compile(r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])')

    @cached(cache={})
    def version(self):
        result = subprocess.run([self.CMD, '-v'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            value = self._sanitise(result.stdout.decode('utf-8').strip())
            return Version(value)

        return Version('N/A')


    def status(self):
        result = subprocess.run([self.CMD, 'get', 'connectionstate'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            conn_status = cast(ConnectionState, self._sanitise(result.stdout.decode('utf-8').strip()))

            if conn_status != 'Connected':
                return StatusResponse(conn_status)
            else:
                server = subprocess.run([self.CMD, 'get', 'region'], stdout=subprocess.PIPE, check = True).stdout.decode('utf-8')
                return StatusResponse(
                        status = conn_status,
                        server = server)

        return StatusResponse(status = 'Failed')

    @cached(cache=TTLCache(maxsize=1, ttl=1800))
    def servers(self):
        servers = {}
        locations: list[str] = []

        result = subprocess.run([self.CMD, 'get', 'regions'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            server_lines = result.stdout.decode('utf-8').splitlines()

            if server_lines:
                for line in server_lines:
                    if line != 'auto':
                        locations.append(self._sanitise(line).strip())
                common = [locations[0]]
                for location in locations[1:]:
                    if len(os.path.commonprefix([*common, location])) > 5:
                        common.append(location)
                    else:
                        country = os.path.commonprefix([re.sub(r"-[0-9]+$", "", x) for x in common])
                        servers[re.sub(r"-?$", "", country)] = [*common]
                        common = [location]
                country = os.path.commonprefix([re.sub(r"-[0-9]+$", "", x) for x in common])
                servers[re.sub(r"-?$", "", country)] = [*common]

        return ServerList(servers)

    def disconnect(self):
        # let's ignore the return code, as it could have not been connected...
        subprocess.run([self.CMD, 'disconnect'], capture_output=False, check = False)

    def connect(self, server: str):
        self.disconnect()

        subprocess.run([self.CMD, 'set', 'region', server], stderr=subprocess.PIPE, check = True)
        subprocess.run([self.CMD, 'connect'], stderr=subprocess.PIPE, check = True)

    def ips(self):
        return IPs(
                vpn_ip=subprocess.run([self.CMD, 'get', 'vpnip'], stdout=subprocess.PIPE, check = True).stdout.decode('utf-8').strip(),
                public_ip=subprocess.run([self.CMD, 'get', 'pubip'], stdout=subprocess.PIPE, check = True).stdout.decode('utf-8').strip(),
                )

    def preferences(self):
        response = {}

        for key in Preferences.__annotations__.keys(): # pylint: disable=no-member
            result = subprocess.run([self.CMD, 'get', key], stdout=subprocess.PIPE, check = False)

            if result.returncode == 0:
                lines = result.stdout.decode('utf-8').splitlines()
                if len(lines) > 0:
                    response[key] = lines if len(lines) > 1 else lines[0]

        return response

    def set_preference(self, name: str, value: str | list[str]):
        cmd = ['sudo', self.CMD] if name.startswith('split') else [self.CMD]
        if isinstance(value, list):
            # quick workaround to deal with multivalues...
            # retrieve the previous values and
            # set only the differences
            # TODO to finish...
            result = subprocess.run(
                    [self.CMD, 'get', name],
                    stderr=subprocess.PIPE,
                    check = True)
            if result.returncode == 0:
                lines = set(result.stdout.decode('utf-8').splitlines())
                values = set(value)
                for v in values.difference(lines):
                    subprocess.run(
                            [*cmd, 'set', name, v],
                            stderr=subprocess.PIPE,
                            check = True)
        else:
            subprocess.run(
                    [*cmd, 'set', name, value],
                    stderr=subprocess.PIPE,
                    check = False)

    def _sanitise(self, value: str):
        return self.ANSI_ESCAPE.sub('', value)

    def _find_servers(self, lines: list[str]):
        index = 0
        while True:
            if index == len(lines):
                return []
            header = self._sanitise(lines[index]).strip()
            if header.startswith('ALIAS'):
                return lines[index:]
            index += 1
