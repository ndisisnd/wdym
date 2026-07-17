# Security policy

## Reporting a vulnerability

Please don't open a public issue for a security problem. Report it privately through
[GitHub's private vulnerability reporting](https://github.com/ndisisnd/wdym/security/advisories/new)
— it goes straight to the maintainer and stays closed until there's a fix.

Include what you can: what the issue is, how to reproduce it, and what an attacker
could do with it. A rough report is more useful than no report.

You'll get an acknowledgment as soon as a maintainer sees it. Once a fix ships,
you'll be credited in the advisory unless you'd rather not be.

## Supported versions

This project is distributed from `main`. Fixes land on `main`; there are no
maintained release branches. Use the latest commit.

## Scope

wdym runs locally inside Claude Code. It installs a `UserPromptSubmit` hook
(`hooks/prompt-detect.py`) that runs on every prompt you submit, a skill that reads
and rewrites that prompt, and an append-only telemetry file (`telemetry.jsonl`) written
into the install directory. It has no server, no network listener, and no credentials.
The realistic surface is what the hook and skill read and write on your machine, plus
the install path — `install.sh` is fetched and piped to a shell (`curl … | bash`), and
it pulls a release tarball over HTTPS.

## Disclosure

Report privately, and please hold off on publishing until a fix is out. Fixed issues
are published as a GitHub advisory with credit to the reporter.
