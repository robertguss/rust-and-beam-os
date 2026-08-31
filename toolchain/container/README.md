# Linux build environment

The builder is
`docker.io/library/python@sha256:c900d35aba5fe4c1dc1cd358408baae2902ff2a2926a1d15cc5002c6061ddb2e`.
It is Python 3.13.7 on Debian Bookworm's buildpack base and includes the native
C/C++ compiler, linker, Make, Autoconf, Perl, Git, curl, OpenSSL headers, and
ncurses headers used by the P003 source-build probe.

Pinned OCI child manifests:

- x86_64 Linux:
  `sha256:dff7bf7639ce459600e6e042228480eb9b6c627ce590e282c9b1d7c03fcad30b`
- AArch64 Linux:
  `sha256:68331cab69c9b5e5ecd0d1d7f59bfcc5179bb790454169661a8beb4f436a45e6`

The index and child digests are immutable; the human-readable tag is not used
for execution. Builder receipts separate host observations from the target
contract. Matching receipts do not claim bit-identical binaries.
