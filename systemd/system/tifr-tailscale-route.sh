#!/usr/bin/bash
# Prefer Tailscale's IPv4 routes over the TIFR default route.
set -euo pipefail
rules=$(/usr/bin/ip -4 rule show)
if ! /usr/bin/grep -Eq '^100:[[:space:]]+from all to 100[.]64[.]0[.]0/10 lookup 52[[:space:]]*$' <<< "$rules"; then
    /usr/bin/ip -4 rule add priority 100 to 100.64.0.0/10 lookup 52
fi
# Migrate the earlier phone-only rule after the broader rule is in place.
if /usr/bin/grep -Eq '^100:[[:space:]]+from all to 100[.]70[.]149[.]97(/32)? lookup 52[[:space:]]*$' <<< "$rules"; then
    /usr/bin/ip -4 rule del priority 100 to 100.70.149.97/32 lookup 52
fi
