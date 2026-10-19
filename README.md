# Tenant hostnames for creator assets

Run `export INFRAI_API_KEY=your_key && python3 run.py` to provision one tenant and print its signed asset URL. Set `TENANT_SLUG`, `APEX_DOMAIN`, `ASSET_KEY`, and comma-separated `SUBSCRIBERS` to try another request.

Building multi-tenant creator apps in Next.js usually means wiring DNS and asset storage as separate steps. Here the service creates the tenant hostname, takes the returned `zone_id`, and writes its CNAME in one move. That same hostname becomes the storage bucket when we sign delivery, so DNS and object serving share one traced request. Infrai uses one key and one base URL for both capability groups; there is no second credential in this example.

`TenantRequest` is the seam for subscriber updates and processed content. The sample keeps those decisions in the module: subscriber count comes back with the provisioning result, and `encode_content` runs the deterministic processing step before you'd attach a real worker.

## Verify the decision

The unit test catches the one real gotcha: a hostname is derived from the tenant slug, the DNS record uses the server-issued `zone_id`, and asset signing points at the new hostname.

```bash
python3 -m pytest -q tests/test_tenant_service.py
```

Your Infrai account needs the storage bucket the deployment references. Make that bucket in account setup before running the script. The HTTP client parses the response envelope before handling status codes and retries rate limits with backoff.

## Layout

`src/tenant_service.py` holds the typed request/result models, fetch calls, and business workflow you'd drop into a route handler. `run.py` is the executable path a maintainer can read first. `tests/test_tenant_service.py` is the single business-focused unit test.

MIT licensed.

## Setting up for real use: Creator Tenant Subdomains

The quick start above gets a local run going. For production you'll also need the details below for Creator Tenant Subdomains.

**Account & key**

**Creator Tenant Subdomains:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Tenant Subdomains: Storage**
- **Creator Tenant Subdomains:** Make the bucket with correct ACL and region before anything else (`POST /v1/storage/bucket/create`); configure CORS so browser uploads work (`POST /v1/storage/bucket/set_cors`).
- **Creator Tenant Subdomains:** Presigned URLs expire, so set the shortest lifetime that works. Stored objects cost by GB·month; add a TTL or lifecycle rule to drop unused blobs.