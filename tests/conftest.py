from dataclasses import dataclass
from typing import Any, Callable
import json
import os
import socket
import subprocess
import time
import pytest

IMAGE_TO_TEST = os.getenv('TARGET_IMAGE', default = 'expressvpn:local')
ACTIVATION_CODE = os.getenv('ACTIVATION_CODE', default = '')


class ContainerException(Exception):
    pass


@dataclass
class Container:
    port: int
    container_id: str
    execute: Callable[[str], subprocess.CompletedProcess]
    inspect: Callable[[], dict[str, Any]]

def _get_free_port():
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _get_container_id():
    return subprocess.run(['docker', 'ps', '-q', '-l'], stdout=subprocess.PIPE, check = True).stdout.decode('utf-8').strip()


def _container_executor(command: str, fail_on_error=True):
    to_exec = ['docker', 'exec', '-t', _get_container_id(), 'bash', '-c', command]

    return subprocess.run(to_exec, stdout=subprocess.PIPE, check=fail_on_error).stdout.decode('utf-8').strip()


def _container_inspector():
    result = subprocess.run(['docker', 'inspect', _get_container_id()], stdout=subprocess.PIPE, check = True)

    return json.loads(result.stdout.decode('utf-8').strip())


def _wait_for_container_to_be_healthy(max_attempts = 30, delay_between_attempts = 1):
    container_id = _get_container_id()
    iterations = 0

    if not container_id:
        raise ContainerException('Container is not running!')

    while True:
        if iterations > max_attempts:
            raise ContainerException(f'Max attempts ({max_attempts}) reached to wait for container to become healthy!')

        result = subprocess.run(['docker', 'inspect', container_id], stdout=subprocess.PIPE, check = False)

        if result.returncode != 0:
            raise ContainerException(f'Container inspection failed: {result.stdout.decode("utf-8").strip()}')

        value = json.loads(result.stdout.decode('utf-8').strip())

        if not value:
            raise ContainerException('Container inspection result was empty!')

        if value[-1].get('State', {}).get('Health', {}).get('Status', 'unhealthy') == 'healthy':
            return

        time.sleep(delay_between_attempts)
        iterations += 1


def _tear_down():
    subprocess.run(['docker', 'rm', '-v', '-f', _get_container_id()], stdout=subprocess.PIPE, check = True)


@pytest.fixture(scope='session', autouse=True)
def container(request):
    request.addfinalizer(_tear_down)

    exposed_port = _get_free_port()
    subprocess.run(
            ['docker',
             'run',
             '-d',
             '--privileged',
             '--cap-add=NET_ADMIN',
             '--device=/dev/net/tun',
             '-e',
             f'ACTIVATION_CODE={ACTIVATION_CODE}',
             '-p',
             f'{exposed_port}:5000',
             IMAGE_TO_TEST
            ],
            stdout=subprocess.PIPE, check = True)

    _wait_for_container_to_be_healthy()

    return Container(port = exposed_port,
                     container_id = _get_container_id(),
                     execute = _container_executor,
                     inspect = _container_inspector)
