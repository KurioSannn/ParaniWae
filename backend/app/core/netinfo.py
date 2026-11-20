"""Penentuan IP klien yang aman terhadap pemalsuan X-Forwarded-For."""

import ipaddress
from functools import lru_cache

from fastapi import Request

from app.core.config import get_settings


@lru_cache
def _networks(cidrs: str) -> tuple:
    out = []
    for part in cidrs.split(","):
        part = part.strip()
        if part:
            out.append(ipaddress.ip_network(part, strict=False))
    return tuple(out)


def _trusted(peer: str, cidrs: str) -> bool:
    try:
        addr = ipaddress.ip_address(peer)
    except ValueError:
        return False
    return any(addr in n for n in _networks(cidrs))


def client_ip(request: Request) -> str:
    """IP klien.

    - Peer langsung BUKAN proxy tepercaya -> abaikan X-Forwarded-For sepenuhnya (anti-spoof).
    - Peer tepercaya -> pakai entri ke-`hops` dari KANAN XFF (ditambahkan proxy kita sendiri);
      entri di kirinya berasal dari klien dan tidak dipercaya.
    """
    s = get_settings()
    peer = request.client.host if request.client else "unknown"
    if not _trusted(peer, s.trusted_proxy_cidrs):
        return peer
    chain = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    hops = max(1, s.trusted_proxy_hops)
    if len(chain) < hops:
        return peer
    cand = chain[-hops]
    try:
        return str(ipaddress.ip_address(cand))
    except ValueError:
        return peer
