import socket
import subprocess


def _is_usable_lan_ip(ip):
    if not ip or ip.startswith("127.") or ip.startswith("169.254."):
        return False
    first = ip.split(".")[0] if "." in ip else ""
    return first in ("10", "172", "192")


def _is_physical_iface(name):
    """Физические LAN-интерфейсы (Ethernet/WiFi) в приоритете над VPN/TAP."""
    low = name.lower()
    if any(k in low for k in ("tap", "vpn", "tun", "teredo", "outline", "ppp", "wintun")):
        return False
    return True


def get_local_ips():
    """Возвращает список (имя_интерфейса, ip) всех активных интерфейсов
    с реальным приватным адресом локальной сети (не VPN/loopback/169.254).
    Физические интерфейсы идут раньше VPN/TAP."""
    result = []
    try:
        out = subprocess.check_output(
            ["ipconfig"],
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            errors="replace",
        )
    except Exception:
        return result

    current_iface = None
    for raw in out.splitlines():
        line = raw.strip()
        low = line.lower()
        # Заголовок адаптера (без ". . .", например "Адаптер Ethernet Ethernet:")
        if ". . ." not in line and line.endswith(":"):
            current_iface = line.rstrip(":")
            continue
        if "ipv4" in low or "ip адрес" in low:
            if ":" not in line:
                continue
            ip = line.split(":", 1)[1].strip()
            if _is_usable_lan_ip(ip):
                result.append((current_iface or "unknown", ip))

    physical = [x for x in result if _is_physical_iface(x[0])]
    virtual = [x for x in result if not _is_physical_iface(x[0])]
    return physical + virtual


def get_local_ip():
    """Возвращает IP локальной сети (реальный LAN интерфейс, не VPN/loopback)."""
    ips = get_local_ips()
    if ips:
        return ips[0][1]
    # Запасной вариант
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if _is_usable_lan_ip(ip):
            return ip
    except OSError:
        pass
    return "127.0.0.1"


def ip_equals_self(ip):
    """Проверяет, принадлежит ли ip этой машине (включая все интерфейсы)."""
    if not ip:
        return False
    if ip.startswith("127."):
        return True
    for _iface, local_ip in get_local_ips():
        if ip == local_ip:
            return True
    return False
