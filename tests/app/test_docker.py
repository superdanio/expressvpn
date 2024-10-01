class TestDockerImage:

    def test_container_is_healthy(self, container):
        value = container.inspect()

        assert value is not None
        assert value[-1].get('State', {}).get('Health', {}).get('Status', 'unhealthy') == 'healthy'

    def test_container_port(self, container):
        container.execute('ss -tulpn | grep LISTEN | grep :5000')

    def test_container_shared_directory(self, container):
        container.execute('test -s /vpn_shared/resolv.conf')
