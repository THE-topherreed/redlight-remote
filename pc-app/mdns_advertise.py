"""Advertises this PC as 'redlight.local' on the LAN so the CYD board
never needs a hardcoded IP address."""

import socket

from zeroconf import Zeroconf, ServiceInfo

HOSTNAME = "redlight"
SERVICE_TYPE = "_http._tcp.local."
SERVICE_NAME = "RedLight." + SERVICE_TYPE


def _local_ip():
    """Best-effort LAN IP: opens a UDP socket to a public address (no
    packets actually sent) purely to ask the OS which interface it would
    route through."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def start_advertising(port):
    zc = Zeroconf()
    ip = _local_ip()
    info = ServiceInfo(
        SERVICE_TYPE,
        SERVICE_NAME,
        addresses=[socket.inet_aton(ip)],
        port=port,
        server=f"{HOSTNAME}.local.",
    )
    zc.register_service(info)
    return zc, info


def stop_advertising(zc, info):
    zc.unregister_service(info)
    zc.close()
