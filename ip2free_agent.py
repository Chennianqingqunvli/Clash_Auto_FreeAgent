from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

BASE_API = "https://api.ip2free.com"
DEFAULT_HEADERS = {
    "webname": "IP2FREE",
    "domain": "www.ip2free.com",
    "lang": "cn",
    "referer": "https://www.ip2free.com/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) ip2free-agent/1.0"
    ),
    "content-type": "text/plain;charset=UTF-8",
    "affid": "",
    "invitecode": "",
    "serviceid": "",
}


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def _credentials() -> tuple[str, str]:
    email = os.environ.get("IP2FREE_EMAIL")
    password = os.environ.get("IP2FREE_PASSWORD")
    if not email or not password:
        raise RuntimeError("Set IP2FREE_EMAIL and IP2FREE_PASSWORD environment variables before running.")
    return email, password


def _login(session: requests.Session) -> str:
    email, password = _credentials()
    payload = {"email": email, "password": password}
    resp = session.post(f"{BASE_API}/api/account/login", data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    body = resp.json()
    token = body.get("data", {}).get("token") or session.cookies.get("Mall-Token")
    if not token:
        raise RuntimeError("Login failed: Mall-Token cookie missing")
    session.headers["x-token"] = token
    session.cookies.set("Mall-Token", token, domain="www.ip2free.com", path="/")
    return token


def _fetch_free_ips(session: requests.Session, max_pages: int = 10, page_size: int = 100) -> list[Dict[str, Any]]:
    results: list[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        payload = {"keyword": "", "country": "", "city": "", "page": page, "page_size": page_size}
        resp = session.post(f"{BASE_API}/api/ip/freeList", data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        body = resp.json()
        free_list = body.get("data", {}).get("free_ip_list") or []
        if not free_list:
            break
        results.extend(free_list)
        if len(free_list) < page_size:
            break
    if not results:
        raise RuntimeError("No free IP returned from API")
    return results


def _build_yaml(proxies: list[Dict[str, Any]]) -> str:
    lines = [
        "port: 7890",
        "socks-port: 7891",
        "mode: Rule",
        "allow-lan: false",
        "log-level: info",
        "",
        "proxies:",
    ]

    proxy_names: list[str] = []
    for proxy in proxies:
        country = proxy.get("country_code", "XX")
        city = proxy.get("city") or "unknown"
        name = f"ip2free-{country}-{city}-{proxy.get('id', 'free')}"
        name = name.replace(" ", "_")
        server = proxy.get("ip", "0.0.0.0")
        port = proxy.get("port", 0)
        username = proxy.get("username", "")
        password = proxy.get("password", "")
        protocol = proxy.get("protocol", "socks5")
        lines.extend(
            [
                f'  - name: "{name}"',
                f"    type: {protocol}",
                f"    server: {server}",
                f"    port: {port}",
                f"    username: {username}",
                f"    password: {password}",
                "",
            ]
        )
        proxy_names.append(name)

    if not proxy_names:
        raise RuntimeError("No proxies to write into YAML")

    lines.extend(
        [
            "proxy-groups:",
            '  - name: "PROXY"',
            "    type: select",
            "    proxies:",
            *[f'      - "{name}"' for name in proxy_names],
            "      - DIRECT",
            "",
            "rules:",
            "  - MATCH,PROXY",
            "",
            "dns:",
            "  enabled: true",
            "  listen: 0.0.0.0:1053",
            "  default-nameserver:",
            "    - 1.1.1.1",
            "    - 8.8.8.8",
            "  nameserver:",
            "    - 1.1.1.1",
            "    - 8.8.8.8",
            "  enhanced-mode: fake-ip",
            "  fake-ip-range: 198.18.0.1/16",
            "  use-hosts: true",
            "",
        ]
    )
    return "\n".join(lines)


def _dest_path() -> Path:
    desktop = Path(os.path.expanduser("~/Desktop"))
    date_name = _dt.date.today().isoformat()
    return desktop / f"{date_name}.yaml"


def main() -> None:
    session = _session()
    _login(session)
    proxies = _fetch_free_ips(session)
    yaml_text = _build_yaml(proxies)
    dest = _dest_path()
    dest.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote {dest} with {len(proxies)} free proxies")


if __name__ == "__main__":
    main()
