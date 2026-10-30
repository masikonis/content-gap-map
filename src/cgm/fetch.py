"""Polite, safe web requests, shared by every step that fetches from the web.

Every request names the tool honestly and waits PAUSE seconds. Page fetches, whose URLs come from
the web and so can't be trusted, also go to public addresses only, are sent to the address that
was checked (so a second lookup can't swap in a private one), respect robots.txt at every redirect
hop, and read at most MAX_BYTES.
"""

import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "content-gap-map/0.1 (+https://github.com/masikonis/content-gap-map)"
PAUSE = 2.0
MAX_BYTES = 2_000_000
MAX_REDIRECTS = 5


def http_client(timeout: float) -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=timeout, trust_env=False)


def public_address(host: str) -> str | None:
    """One address for the host, only if every address it resolves to is on the public internet."""
    try:
        addresses = sorted({info[4][0] for info in socket.getaddrinfo(host, None)})
    except (socket.gaierror, UnicodeError):
        return None
    if not addresses or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addresses):
        return None
    return addresses[0]


class NotPublic(Exception):
    pass


class PageFetcher:
    """Fetches pages from untrusted URLs, following the rules in this module's docstring."""

    def __init__(self, http: httpx.Client):
        self.http, self.robots = http, {}

    def read(self, url: str) -> tuple[int, str, str | None]:
        parts = urlsplit(url)
        address = public_address(parts.hostname or "")
        if address is None:
            raise NotPublic(url)
        ip = f"[{address}]" if ":" in address else address
        pinned = parts._replace(netloc=f"{ip}:{parts.port}" if parts.port else ip).geturl()
        host = f"{parts.hostname}:{parts.port}" if parts.port else parts.hostname
        extensions = {"sni_hostname": parts.hostname} if parts.scheme == "https" else {}
        time.sleep(PAUSE)
        with self.http.stream("GET", pinned, headers={"Host": host}, extensions=extensions) as response:
            body = b""
            for chunk in response.iter_bytes():
                body += chunk
                if len(body) >= MAX_BYTES:
                    break
            text = body[:MAX_BYTES].decode(response.encoding or "utf-8", errors="replace")
            return response.status_code, text, response.headers.get("location")

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self.robots:
            rules = RobotFileParser()
            try:
                status, text, _ = self.read(f"{host}/robots.txt")
                rules.parse(text.splitlines() if status == 200 else [])
            except (httpx.HTTPError, NotPublic):
                rules.parse([])
            self.robots[host] = rules
        return self.robots[host].can_fetch(USER_AGENT, url)

    def fetch(self, url: str) -> tuple[int | None, str]:
        """Follows redirects by hand, re-checking each hop. Returns (status, text) or (None, reason)."""
        for _ in range(MAX_REDIRECTS + 1):
            parts = urlsplit(url)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                return None, "not a web address"
            try:
                if not self.allowed(url):
                    return None, "robots.txt forbids crawlers"
                status, text, location = self.read(url)
            except NotPublic:
                return None, "not a public address"
            if status in (301, 302, 303, 307, 308) and location:
                url = urljoin(url, location)
                continue
            return status, text
        return None, "too many redirects"
