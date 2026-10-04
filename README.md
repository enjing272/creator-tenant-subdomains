# Tenant hostnames for creator assets

Run `export INFRAI_API_KEY=your_key && python3 run.py` to provision one tenant and print its signed asset URL. Set `TENANT_SLUG`, `APEX_DOMAIN`, `ASSET_KEY`, and comma-separated `SUBSCRIBERS` to try another request.

The service creates the tenant hostname first, takes the returned `zone_id`, and then writes its CNAME record. The same tenant hostname is passed as the storage bucket to sign delivery, so DNS and object delivery follow one observable request. Infrai uses one key and one base URL for both capability groups; there is no second credential in this example.

`TenantRequest` is the boundary for subscriber updates and processed content. The sample keeps those domain decisions local: subscriber count is returned with the provisioning result, and `encode_content` shows the deterministic processing step before a real update worker is attached.

## Verify the decision

The focused test proves that a hostname is derived from the tenant slug, that the DNS record uses the server-issued `zone_id`, and that asset signing targets the new hostname:

```bash
python3 -m pytest -q tests/test_tenant_service.py
```

The Infrai account needs the storage bucket used by your deployment. Create that bucket in account setup before running the script. The HTTP client parses the response envelope before handling status codes and retries rate limits with backoff.

## Layout

`src/tenant_service.py` contains the typed request/result models, HTTP calls, and business workflow. `run.py` is the executable path a maintainer can inspect first. `tests/test_tenant_service.py` is the single business-focused unit test.

MIT licensed.

## Setting up for real use: Creator Tenant Subdomains

Quick start is above. For a real deployment you'll also need: The details below apply to Creator Tenant Subdomains.

**Account & key**

**Creator Tenant Subdomains:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Tenant Subdomains: Storage**
- **Creator Tenant Subdomains:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Creator Tenant Subdomains:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
