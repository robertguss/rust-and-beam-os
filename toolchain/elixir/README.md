# Elixir toolchain

Elixir 1.20.4 is selected at upstream commit
`759443e724f55bf58e71c0603644e99058918d52`. Its immutable commit archive has
SHA-256 `6a2451e8655554edbbcec952f545ac2f8f25778b3883166c7cc724d6cf31d298`.

Elixir 1.20 supports OTP 27–29. The P003 probe builds with deterministic
compiler options against the selected OTP 29.0.5 installation, then compiles,
tests, and runs `beam/toolchain_smoke` without Hex dependencies or network
access. P002 owns the complete supervised `runtime_lab` workload.
