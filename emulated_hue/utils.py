
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from typing import Union
import socket
import slugify as unicode_slug
import json
import os
import logging
import tempfile

_LOGGER = logging.getLogger(__name__)

# IP addresses of loopback interfaces
LOCAL_IPS = (ip_address("127.0.0.1"), ip_address("::1"))

# RFC1918 - Address allocation for Private Internets
LOCAL_NETWORKS = (
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
)


def is_local(address: Union[IPv4Address, IPv6Address]) -> bool:
    """Check if an address is local."""
    return address in LOCAL_IPS or any(address in network for network in LOCAL_NETWORKS)


# Taken from: http://stackoverflow.com/a/11735897
def get_local_ip() -> str:
    """Try to determine the local IP address of the machine."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Use Google Public DNS server to determine own IP
        sock.connect(("8.8.8.8", 80))

        return sock.getsockname()[0]  # type: ignore
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1"
    finally:
        sock.close()


def slugify(text: str) -> str:
    """Slugify a given text."""
    return unicode_slug.slugify(text, separator="_")  # type: ignore


def update_dict(dict1, dict2):
    """Helper to update dict1 with values of dict2."""
    for key, value in dict2.items():
        if key in dict1 and isinstance(value, dict):
            update_dict(dict1[key], value)
        else:
            dict1[key] = value


def load_json(filename: str):
    """Load JSON from file."""
    try:
        with open(filename, encoding="utf-8") as fdesc:
            return json.loads(fdesc.read())  # type: ignore
    except (FileNotFoundError, ValueError, OSError) as error:
        _LOGGER.debug("Loading %s failed: %s", filename, error)
        return {}


def save_json(filename: str, data: dict):
    """Save JSON data to a file."""
    tmp_filename = ""
    tmp_path = os.path.split(filename)[0]
    try:
        json_data = json.dumps(data, sort_keys=True, indent=4)
        # Modern versions of Python tempfile create this file with mode 0o600
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=tmp_path, delete=False
        ) as fdesc:
            fdesc.write(json_data)
            tmp_filename = fdesc.name
        os.replace(tmp_filename, filename)
    except (TypeError, OSError):
        _LOGGER.exception("Failed to serialize to JSON: %s", filename)
    finally:
        if os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except OSError as err:
                # If we are cleaning up then something else went wrong, so
                # we should suppress likely follow-on errors in the cleanup
                _LOGGER.error("JSON replacement cleanup failed: %s", err)