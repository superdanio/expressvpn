import re
import shutil
import subprocess
from cachetools import cached, TTLCache

from models import Configuration, ServerDetails, ServerList, Status, StatusResponse, Version

class Client:

    CMD = 'expressvpn'
    ANSI_ESCAPE = re.compile(r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])')

    @cached(cache={})
    def version(self):
        result = subprocess.run([self.CMD, '-v'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            value = self._sanitise(result.stdout.decode('utf-8').strip())
            version = re.search('^expressvpn version (.+) \\([^\\)]+\\)$', value)
            return Version(version.group(1) if version else value)

        return Version('N/A')


    def status(self):
        result = subprocess.run([self.CMD, 'status'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            conn_status = self._sanitise(result.stdout.decode('utf-8').strip())

            if 'Not connected' in conn_status:
                return StatusResponse(status = Status.DISCONNECTED)

            if 'Connected to ' in conn_status:
                server = re.search('Connected to ([^\n\r]+)', conn_status, re.MULTILINE)
                return StatusResponse(
                        status = Status.CONNECTED,
                        server = None if server is None else server.group(1))

            return StatusResponse(status = Status.UNABLE_TO_CONNECT)

        return StatusResponse(status = Status.FAILED)

    @cached(cache=TTLCache(maxsize=1, ttl=1800))
    def servers(self):
        last_country = None
        servers = {}

        result = subprocess.run([self.CMD, 'list', 'all'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            server_lines = self._find_servers(result.stdout.decode('utf-8').splitlines())

            if server_lines:
                header = server_lines[0]
                country_index = header.index('COUNTRY')
                location_index = header.index('LOCATION')
                recommended_index = header.index('RECOMMENDED')

                for line in server_lines[2:]:
                    row = self._sanitise(line)
                    alias = row[:country_index].strip()
                    country = row[country_index:location_index].strip()
                    location = row[location_index:recommended_index].strip()
                    recommended = row[recommended_index:].strip()

                    if country:
                        last_country = country
                        servers[last_country] = []

                    servers[last_country].append(ServerDetails(
                        alias = alias,
                        location = location,
                        recommended = 'Y' == recommended))

        return ServerList(servers)

    def disconnect(self):
        # let's ignore the return code, as it could have not been connected...
        subprocess.run([self.CMD, 'disconnect'], capture_output=False, check = False)
        self._refresh_dns_entries()

    def connect(self, server: str):
        self.disconnect()

        result = subprocess.run([self.CMD, 'connect', server], stderr=subprocess.PIPE, check = False)
        if result.returncode != 0:
            raise ValueError(self._sanitise(result.stderr.decode('utf-8').strip()))
        self._refresh_dns_entries()

    def refresh(self):
        subprocess.run([self.CMD, 'refresh'], capture_output=False, check = False)
        self._refresh_dns_entries()

    def preferences(self):
        response = Configuration()

        result = subprocess.run([self.CMD, 'preferences'], stdout=subprocess.PIPE, check = False)

        if result.returncode == 0:
            for line in result.stdout.decode('utf-8').splitlines():
                pref = re.search('([^\\s]+)\\s+(.+)', self._sanitise(line).strip())
                if pref is not None:
                    response.preferences[pref.group(1).strip()] = pref.group(2).strip()

        return response

    def set_preference(self, name: str, value: str):
        result = subprocess.run(
                [self.CMD, 'preferences', 'set', name, value],
                stderr=subprocess.PIPE,
                check = False)

        if result.returncode != 0:
            raise ValueError(self._sanitise(result.stderr.decode('utf-8').strip()))

    def _refresh_dns_entries(self):
        shutil.copyfile('/etc/resolv.conf', '/vpn_shared/resolv.conf')

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
