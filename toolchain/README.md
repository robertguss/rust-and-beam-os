# Toolchain

`contract.json` is the Phase 0 host/target contract and `sources.lock.json` is
its complete content-addressed source closure. `TOOLCHAIN.md` is generated from
those machine-readable files. `bootstrap-tools.json` remains the small
repository bootstrap subset.

Run `just toolchain-bootstrap` once to populate `target/toolchain-cache`, pull
the OCI builder by digest, compare two fresh Linux-builder receipts, and build
the selected OTP/Elixir pair with networking disabled. Later verification is
offline:

```sh
just toolchain-report
just toolchain-verify
```

The large source mirror is deliberately not committed. Cache paths are the
SHA-256 values from `sources.lock.json`, so missing or changed bytes fail before
compilation. ADR 0001 records the selection and its residual risks.
