# RB-T-ORBSETUP evidence

The lifecycle scripts were exercised in this orb with an empty temporary HOME to
model a fresh activation. `setup-fresh.txt` records installation and the full
repository check in 68.89 seconds. Rustup prints a harmless HOME/passwd-home
diagnostic because the test deliberately uses an isolated HOME; a normal orb
uses `/home/user` for both values.

The same isolated HOME was reused without modification for `setup-warm.txt`. The
1.93-second warm pass installed no package, Rust component, or `just` binary,
and the profile marker remained unique. `login-shell.txt` proves a minimal
non-interactive login shell receives the Cargo tool path. `resume.txt` records a
0.10-second wake check with no installation or network work. `final-check.txt`
records the final repository checks from a clean login-shell environment.

No database, service, environment template, authentication, or secret is
required by the current repository. Later ready tasks must extend setup when
they add a selected dependency rather than installing future candidates now.
