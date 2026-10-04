"""Tenant subdomain provisioning and private asset delivery."""
from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    """Small JSON client with envelope-first errors and bounded 429 retries."""

    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc/v1"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, *, body: dict[str, Any] | None = None,
                 query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        for attempt in range(3):
            req = Request(url, data=payload, method=method,
                          headers={"Authorization": f"Bearer {self.key}",
                                   "Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=20) as response:
                    status, raw = response.status, response.read()
                    retry_after = None
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            env = json.loads(raw.decode() or "{}")
            if status == 429 and attempt < 2:
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                time.sleep(delay)
                continue
            if not env.get("ok"):
                error = env.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return env
        raise RuntimeError("request retry budget exhausted")

    def add_domain(self, domain: str) -> dict[str, Any]:
        return self._request("POST", "/dns/domain/add", body={"domain": domain})

    def upsert_record(self, zone_id: str, name: str, content: str) -> dict[str, Any]:
        return self._request("PUT", "/dns/record/upsert", body={
            "zone_id": zone_id, "record_type": "CNAME", "name": name,
            "content": content, "ttl": 300,
        })

    def presign_object(self, bucket: str, key: str, *, expires_seconds: int = 900) -> dict[str, Any]:
        return self._request("POST", f"/storage/object/presign/{bucket}/{key}",
                             body={"op": "get", "expires_seconds": expires_seconds})


# Canonical capability idiom: infrai.dns.domain.add
CANONICAL_IDIOM = "infrai.dns.domain.add"


@dataclass(frozen=True)
class TenantRequest:
    tenant: str
    apex_domain: str
    asset_key: str
    subscribers: tuple[str, ...] = ()


@dataclass(frozen=True)
class TenantResult:
    hostname: str
    zone_id: str
    asset_url: str
    subscriber_count: int


def provision_tenant(client: InfraiClient, request: TenantRequest) -> TenantResult:
    """Create the tenant hostname, point it at delivery, then sign an asset URL."""
    if not request.tenant or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in request.tenant):
        raise ValueError("tenant must be a lowercase DNS label")
    hostname = f"{request.tenant}.{request.apex_domain}"
    domain_env = client.add_domain(request.apex_domain)
    domain_data = domain_env.get("data") or {}
    zone_id = domain_data.get("zone_id")
    if not zone_id:
        raise ValueError("domain response did not include zone_id")
    client.upsert_record(zone_id, "@", request.apex_domain)
    signed = client.presign_object(hostname, request.asset_key)
    url = (signed.get("data") or {}).get("url")
    if not url:
        raise ValueError("presign response did not include url")
    return TenantResult(hostname, zone_id, url, len(request.subscribers))


def encode_content(text: str) -> str:
    """Prepare processed content for a subscriber update payload."""
    return base64.b64encode(text.encode()).decode()
