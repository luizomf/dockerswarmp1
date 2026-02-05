# dockerswarmp1

## Nodes

| Node | Public IP | WireGuard IP | Domain |
| --- | --- | --- | --- |
| kvm2 | 76.13.71.178 | 10.100.0.2 | inprod.cloud |
| kvm4 | 191.101.70.130 | 10.100.0.4 | otaviomiranda.cloud |
| kvm8 | 89.116.73.152 | 10.100.0.8 | myswarm.cloud |

Notes

- Only `kvm8` is exposed to the public internet (Traefik edge).
- `app.myswarm.cloud` is the single public domain for frontend and API.
- `kvm2` and `kvm4` are locked down by the firewall.
