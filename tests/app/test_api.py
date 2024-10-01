import re
import requests

class TestApi:

    def test_version(self, container):
        assert re.match(r'\d+\.\d+\.\d+\.\d+',
                        requests.get(url=self._api(container.port, 'version'), timeout=5).json()['version'])

    def test_connection(self, container):
        assert requests.get(url=self._api(container.port, 'status'), timeout=5).json()['status'] == 'DISCONNECTED'

        requests.post(url=self._api(container.port, 'connect/smart'), timeout=5)

        assert requests.get(url=self._api(container.port, 'status'), timeout=5).json()['status'] == 'CONNECTED'

        requests.post(url=self._api(container.port, 'disconnect'), timeout=5)

        assert requests.get(url=self._api(container.port, 'status'), timeout=5).json()['status'] == 'DISCONNECTED'

    def test_servers(self, container):
        response = requests.get(url=self._api(container.port, 'servers'), timeout=5).json()

        assert len(response['servers']['Smart Location']) == 1
        assert response['servers']['Smart Location'][0]['alias'] == 'smart'
        assert len(response['servers']) > 1

    def test_preferences(self, container):
        prefs = requests.get(url=self._api(container.port, 'preferences'), timeout=5).json()['preferences']

        assert len(prefs) > 0

        pref = prefs['auto_connect']
        requests.post(url=self._api(container.port, f'preferences/auto_connect/{"true" if pref == "false" else "false"}'), timeout=5)

        new_prefs = requests.get(url=self._api(container.port, 'preferences'), timeout=5).json()['preferences']

        assert len(prefs) == len(new_prefs)
        assert new_prefs['auto_connect'] == ("true" if pref == "false" else "false")

    def _api(self, port, path):
        return f'http://localhost:{port}/api/{path}'
