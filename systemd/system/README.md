# TIFR VPN and Tailscale IPv4 routing

This system service adds an IPv4 policy rule at boot:

```sh
ip -4 rule add priority 100 to 100.64.0.0/10 lookup 52
```

Priority 100 precedes strongSwan's table-220 rule. Table 52 is maintained by
Tailscale and contains routes to tailnet devices. The helper checks for the exact
existing rule before adding it, so enabling or restarting the service does
not duplicate the manually added rule. Once the broader rule is present, it
removes the earlier phone-only rule for `100.70.149.97/32` if present.
This covers Tailscale IPv4 addresses, not IPv6 or advertised subnet routes
outside this range. It uses the routes Tailscale supplies, and does not make
offline devices reachable or change Tailscale access controls. If table 52
has no matching route, Linux continues to the subsequent routing rules.

A normal user service cannot administer kernel routing rules. This system
service runs briefly as root at boot; it does not run a background monitor.
It does not start a VPN or SSH connection. The rule persists after the helper
exits, but if another program removes it, restart the service to reapply it.

Install from this checkout (requires your sudo password):

```sh
sudo install -Dm755 /home/soham/projects/HyprLife/systemd/system/tifr-tailscale-route.sh /usr/local/libexec/tifr-tailscale-route
sudo install -Dm644 /home/soham/projects/HyprLife/systemd/system/tifr-tailscale-route.service /etc/systemd/system/tifr-tailscale-route.service
sudo systemctl daemon-reload
sudo systemctl enable --now tifr-tailscale-route.service
sudo systemctl restart tifr-tailscale-route.service
```

Verify with Tailscale and TIFR connected:

```sh
systemctl status tifr-tailscale-route.service
ip -4 rule show
ip -4 route get 100.70.149.97
```

The restart applies the updated helper even if the service was already active.
Expect `active (exited)`, a priority-100 rule for `100.64.0.0/10`, and a route
using `tailscale0`, table `52`, for a known peer.

To uninstall and remove the current rule:

```sh
sudo systemctl disable --now tifr-tailscale-route.service
sudo rm /etc/systemd/system/tifr-tailscale-route.service /usr/local/libexec/tifr-tailscale-route
sudo systemctl daemon-reload
sudo ip -4 rule del priority 100 to 100.64.0.0/10 lookup 52
```

Stopping the service alone intentionally leaves the active rule in place so
it does not interrupt an SSH session. The final command above removes it;
omit that command if you want the current rule to remain until reboot.
