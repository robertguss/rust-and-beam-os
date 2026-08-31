# OTP toolchain

OTP 29.0.5 is selected at upstream commit
`5cf5f9725452f4e1b6a4890e8ff0305d76924b98`. The official source release has
SHA-256 `86f6f40d4638852b0383235b02a70d8450184e441e83a06a108bf8e5bf1b2e04`.

The P003 compatibility probe configures
`--without-javac --without-odbc --without-wx`, retains OpenSSL and terminal
support, builds from source inside the pinned Linux OCI image, and installs only
into the transient verification directory. P005 owns the separate AArch64-musl
ERTS profile and artifact.
