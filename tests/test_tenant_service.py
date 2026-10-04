from src.tenant_service import TenantRequest, provision_tenant


class FakeClient:
    def __init__(self):
        self.calls = []

    def add_domain(self, domain):
        self.calls.append(("domain", domain))
        return {"ok": True, "data": {"zone_id": "zone-7"}}

    def upsert_record(self, zone_id, name, content):
        self.calls.append(("record", zone_id, name, content))
        return {"ok": True, "data": {}}

    def presign_object(self, bucket, key, expires_seconds=900):
        self.calls.append(("presign", bucket, key))
        return {"ok": True, "data": {"url": "https://signed.test/a"}}


def test_provision_uses_zone_id_before_record_and_tenant_hostname_for_assets():
    client = FakeClient()
    result = provision_tenant(client, TenantRequest("studio-a", "creators.example.com", "guide.pdf", ("a", "b")))
    assert result.hostname == "studio-a.creators.example.com"
    assert result.subscriber_count == 2
    assert client.calls == [
        ("domain", "creators.example.com"),
        ("record", "zone-7", "@", "creators.example.com"),
        ("presign", "studio-a.creators.example.com", "guide.pdf"),
    ]
