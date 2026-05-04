# SPF Record Reference

## Contents

- [SPF Syntax](#spf-syntax)
- [Common Mechanisms](#common-mechanisms)
- [Qualifiers](#qualifiers)
- [Modifiers](#modifiers)
- [Common Issues](#common-issues)
- [Validation Checklist](#validation-checklist)

## SPF Syntax

SPF records are TXT records starting with `v=spf1` followed by mechanisms and modifiers:

```
v=spf1 [mechanisms] [modifiers]
```

Example:
```
v=spf1 ip4:192.0.2.0/24 include:_spf.google.com -all
```

## Common Mechanisms

| Mechanism | Description | Example |
|-----------|-------------|---------|
| `all` | Matches everything (usually last) | `-all` |
| `ip4` | IPv4 address or CIDR range | `ip4:192.0.2.1` or `ip4:192.0.2.0/24` |
| `ip6` | IPv6 address or CIDR range | `ip6:2001:db8::/32` |
| `a` | A record of domain | `a` or `a:example.com` |
| `mx` | MX records of domain | `mx` or `mx:example.com` |
| `include` | Include another domain's SPF | `include:_spf.google.com` |
| `exists` | Check if A record exists | `exists:%{i}.spf.example.com` |
| `ptr` | PTR record check (deprecated) | `ptr:example.com` |

## Qualifiers

Prefix mechanisms with qualifiers to specify pass/fail behavior:

| Qualifier | Result | Meaning |
|-----------|--------|---------|
| `+` (default) | Pass | Allow mail |
| `-` | Fail | Reject mail |
| `~` | SoftFail | Accept but mark suspicious |
| `?` | Neutral | No policy statement |

## Modifiers

| Modifier | Description | Example |
|----------|-------------|---------|
| `redirect` | Use another domain's SPF entirely | `redirect=_spf.example.com` |
| `exp` | Explanation for failures | `exp=explain.example.com` |

## Common Issues

### DNS Lookup Limit Exceeded

SPF allows maximum 10 DNS lookups. Each of these counts:
- `include`
- `a` (when resolving)
- `mx`
- `ptr`
- `exists`
- `redirect`

**Does NOT count:** `ip4`, `ip6`, `all`

Check lookup count:
```bash
# Using dig
dig +short TXT example.com | grep spf

# Count includes (each is 1+ lookups)
# Nested includes also count toward the limit
```

### Multiple SPF Records

Only ONE SPF record allowed per domain. Multiple records cause `permerror`.

```bash
# Check for multiple SPF records
dig +short TXT example.com | grep "v=spf1"
# Should return exactly one result
```

### Missing `-all` or `~all`

Records without `all` mechanism are incomplete. Always end with:
- `-all` (strict: reject unauthorized)
- `~all` (soft: mark but accept)

### Overly Permissive `+all`

Never use `+all` - it allows anyone to send as your domain.

### Include Chains Too Deep

Nested includes can exceed lookup limit. Flatten when possible.

### PTR Mechanism

`ptr` is deprecated and slow. Replace with `ip4`/`ip6` where possible.

## Validation Checklist

1. **Single record**: Only one `v=spf1` record exists
2. **Syntax valid**: Starts with `v=spf1`, ends with `all` mechanism
3. **Lookup count**: Total DNS lookups <= 10
4. **No deprecated**: Avoid `ptr` mechanism
5. **Not permissive**: Never `+all`
6. **Record length**: Under 255 chars per string (can be split)
7. **Covers senders**: All legitimate sending IPs/services included

## Provider SPF Includes

Common services to include:

| Provider | Include |
|----------|---------|
| Google Workspace | `include:_spf.google.com` |
| Microsoft 365 | `include:spf.protection.outlook.com` |
| Amazon SES | `include:amazonses.com` |
| Mailchimp | `include:servers.mcsv.net` |
| SendGrid | `include:sendgrid.net` |
| Salesforce | `include:_spf.salesforce.com` |
