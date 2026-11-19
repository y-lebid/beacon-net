# Roast levels

Beacon assigns a roast level to each observed remote socket using the process trust list, remote port, and socket state:

- `BURNT`: the process is not in the trust list, including when Beacon cannot read its name.
- `CRISPY`: the process is trusted but uses a remote port other than `80`, `443`, or `53`.
- `SIZZLING`: the process is trusted, uses remote port `80`, `443`, or `53`, and the socket is `ESTABLISHED`.
- `RAW`: the process is trusted, uses remote port `80`, `443`, or `53`, and the socket is in another state.

The order matters: an untrusted process is always `BURNT`; a trusted process on a non-standard port is `CRISPY`, even when its socket is established.
