"""
Test DNS zone data for evaluating dns-troubleshooter skill.

Each zone represents a specific test scenario with expected diagnoses.
"""

# Test domain suffix - all test records use this
TEST_DOMAIN = "dnstest.local"


def zone(name: str) -> str:
    """Helper to create full zone name."""
    return f"{name}.{TEST_DOMAIN}"


# =============================================================================
# SPF Test Scenarios
# =============================================================================

SPF_ZONES = {
    # Valid SPF record
    zone("spf-valid"): {
        "A": ["192.0.2.1"],
        "TXT": ["v=spf1 ip4:192.0.2.0/24 include:_spf.google.com -all"],
    },
    # Multiple SPF records (invalid - causes permerror)
    zone("spf-multiple"): {
        "A": ["192.0.2.2"],
        "TXT": [
            "v=spf1 include:_spf.google.com -all",
            "v=spf1 include:sendgrid.net -all",
        ],
    },
    # Overly permissive +all (insecure)
    zone("spf-permissive"): {
        "A": ["192.0.2.3"],
        "TXT": ["v=spf1 +all"],
    },
    # Missing -all or ~all (incomplete)
    zone("spf-incomplete"): {
        "A": ["192.0.2.4"],
        "TXT": ["v=spf1 ip4:192.0.2.0/24"],
    },
    # Softfail ~all (valid but permissive)
    zone("spf-softfail"): {
        "A": ["192.0.2.5"],
        "TXT": ["v=spf1 ip4:192.0.2.0/24 ~all"],
    },
    # Deprecated ptr mechanism
    zone("spf-deprecated"): {
        "A": ["192.0.2.6"],
        "TXT": ["v=spf1 ptr:example.com -all"],
    },
    # Too many DNS lookups (>10 includes)
    zone("spf-too-many-lookups"): {
        "A": ["192.0.2.7"],
        "TXT": [
            "v=spf1 "
            "include:a.test "
            "include:b.test "
            "include:c.test "
            "include:d.test "
            "include:e.test "
            "include:f.test "
            "include:g.test "
            "include:h.test "
            "include:i.test "
            "include:j.test "
            "include:k.test "
            "-all"
        ],
    },
}


# =============================================================================
# Record Conflict Test Scenarios
# =============================================================================

CONFLICT_ZONES = {
    # CNAME with A record at same name (invalid)
    zone("cname-conflict"): {
        "A": ["192.0.2.10"],
        "CNAME": ["target.example.com."],
    },
    # Multiple A records (valid - load balancing)
    zone("multi-a"): {
        "A": ["192.0.2.11", "192.0.2.12", "192.0.2.13"],
    },
    # Duplicate MX with same priority
    zone("duplicate-mx"): {
        "A": ["192.0.2.14"],
        "MX": [(10, "mail1.example.com."), (10, "mail2.example.com.")],
    },
    # Valid MX with different priorities
    zone("valid-mx"): {
        "A": ["192.0.2.15"],
        "MX": [(10, "mail1.example.com."), (20, "mail2.example.com.")],
    },
}


# =============================================================================
# Delegation Test Scenarios
# =============================================================================

DELEGATION_ZONES = {
    # Properly configured zone with NS records
    zone("valid-delegation"): {
        "A": ["192.0.2.20"],
        "NS": [f"ns1.{zone('valid-delegation')}.", f"ns2.{zone('valid-delegation')}."],
    },
    f"ns1.{zone('valid-delegation')}": {
        "A": ["192.0.2.53"],
    },
    f"ns2.{zone('valid-delegation')}": {
        "A": ["192.0.2.54"],
    },
    # Zone with NS pointing to non-existent server
    zone("broken-ns"): {
        "A": ["192.0.2.21"],
        "NS": ["ns1.nonexistent.invalid."],
    },
}


# =============================================================================
# TTL / Caching Test Scenarios
# =============================================================================

TTL_ZONES = {
    # These would need custom TTL support in the server
    # For now, just test that records exist
    zone("low-ttl"): {
        "A": ["192.0.2.30"],
    },
    zone("high-ttl"): {
        "A": ["192.0.2.31"],
    },
}


# =============================================================================
# Combined Zone Data
# =============================================================================

def get_all_zones() -> dict:
    """Return all test zones combined."""
    zones = {}
    zones.update(SPF_ZONES)
    zones.update(CONFLICT_ZONES)
    zones.update(DELEGATION_ZONES)
    zones.update(TTL_ZONES)

    # Add SOA and NS for the base test domain
    zones[TEST_DOMAIN] = {
        "SOA": [("ns1." + TEST_DOMAIN, "admin." + TEST_DOMAIN, 1, 3600, 600, 86400, 300)],
        "NS": [f"ns1.{TEST_DOMAIN}.", f"ns2.{TEST_DOMAIN}."],
    }
    zones[f"ns1.{TEST_DOMAIN}"] = {"A": ["127.0.0.1"]}
    zones[f"ns2.{TEST_DOMAIN}"] = {"A": ["127.0.0.1"]}

    return zones


# Test scenario metadata for evals
SCENARIOS = {
    "spf-valid": {
        "zone": zone("spf-valid"),
        "category": "spf",
        "expected_diagnosis": "valid",
        "description": "Valid SPF record with ip4 range and include",
    },
    "spf-multiple": {
        "zone": zone("spf-multiple"),
        "category": "spf",
        "expected_diagnosis": "invalid",
        "description": "Multiple SPF records causing permerror",
    },
    "spf-permissive": {
        "zone": zone("spf-permissive"),
        "category": "spf",
        "expected_diagnosis": "insecure",
        "description": "SPF with +all allows anyone to spoof",
    },
    "spf-incomplete": {
        "zone": zone("spf-incomplete"),
        "category": "spf",
        "expected_diagnosis": "incomplete",
        "description": "SPF missing -all or ~all mechanism",
    },
    "spf-deprecated": {
        "zone": zone("spf-deprecated"),
        "category": "spf",
        "expected_diagnosis": "warning",
        "description": "SPF using deprecated ptr mechanism",
    },
    "spf-too-many-lookups": {
        "zone": zone("spf-too-many-lookups"),
        "category": "spf",
        "expected_diagnosis": "invalid",
        "description": "SPF exceeds 10 DNS lookup limit",
    },
    "cname-conflict": {
        "zone": zone("cname-conflict"),
        "category": "conflict",
        "expected_diagnosis": "invalid",
        "description": "CNAME and A record at same name",
    },
    "multi-a": {
        "zone": zone("multi-a"),
        "category": "conflict",
        "expected_diagnosis": "valid",
        "description": "Multiple A records for load balancing",
    },
    "duplicate-mx": {
        "zone": zone("duplicate-mx"),
        "category": "conflict",
        "expected_diagnosis": "warning",
        "description": "MX records with same priority",
    },
}
