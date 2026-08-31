# RB-T-P001 evidence

`bootstrap-transcript.txt` records `./scripts/bootstrap.sh` from a fresh clone
of commit `c2b6e8bc115bbe2974cdc4b9ad235a15eae968dd` in the remote Linux orb.
Empty temporary `CARGO_HOME` and `RUSTUP_HOME` directories made tool
installation independent of the original checkout. The command verified the
pinned `rustup-init`, disabled rustup self-update, installed Rust 1.89.0 and
`just` 1.42.4, and completed `just check`.

`environment.json` records the non-secret host/tool identity. This is scaffold
evidence for repository bootstrap only. It does not freeze P003's complete
toolchain and is not custom-OS target evidence.
