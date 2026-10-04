import json
import os

from src.tenant_service import InfraiClient, TenantRequest, encode_content, provision_tenant


def main() -> None:
    client = InfraiClient()
    request = TenantRequest(
        tenant=os.environ.get("TENANT_SLUG", "studio-a"),
        apex_domain=os.environ.get("APEX_DOMAIN", "creators.example.com"),
        asset_key=os.environ.get("ASSET_KEY", "welcome.txt"),
        subscribers=tuple(filter(None, os.environ.get("SUBSCRIBERS", "alice@example.com").split(","))),
    )
    result = provision_tenant(client, request)
    print(json.dumps({"tenant": result.hostname, "asset_url": result.asset_url,
                      "subscriber_count": result.subscriber_count,
                      "processed_preview": encode_content("welcome")}, indent=2))


if __name__ == "__main__":
    main()
