<div align="center">

<img src="assets/logo.svg" alt="Rewind Bulk Creator logo" width="150" />

# Rewind Bulk Creator

**Bulk-create Rewind.ai accounts, auto-verify them, and mint an API key for each — from a single command.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-3DA639?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![Inboxes](https://img.shields.io/badge/Inboxes-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![Dependencies](https://img.shields.io/badge/Dependencies-requests-2496ED?style=flat-square)](requirements.txt)
[![Status](https://img.shields.io/badge/Status-Active-22C55E?style=flat-square)]()
[![Made with](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-EF4444?style=flat-square)]()

[English](README.md) · [Español](docs/README.es.md) · [Português](docs/README.pt.md) · [Deutsch](docs/README.de.md) · [日本語](docs/README.ja.md) · [中文](docs/README.zh.md)

</div>

---

## Overview

Rewind Bulk Creator is a small, dependency-light Python CLI that automates the
whole Rewind.ai onboarding flow: it provisions disposable inboxes on
[mail.tm](https://mail.tm/), registers a Rewind.ai account for each one, waits
for the verification email, clicks the verification link, and finally creates a
randomly-named API key. Every account and key is written to disk as JSON, CSV
and a plain `email:key` list.

It talks directly to the documented HTTP endpoints, so there is no browser, no
headless driver and no Selenium to install.

## Features

- One command to create any number of accounts.
- Disposable inboxes via mail.tm — nothing to configure.
- Automatic email verification (reads the token from the inbox).
- Random, human-readable API key names (`key-cobalt-falcon-4f2a`).
- Random strong passwords, or pin your own with `--password`.
- Graceful rate-limit handling with an optional wait-and-retry mode.
- Outputs JSON, CSV and `email:key` text for easy piping.
- Dry-run mode to plan a batch with no network calls.

## Quick start

```bash
git clone https://github.com/<you>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# Create 5 verified accounts, each with its own API key
python rewind_bulk.py --count 5
```

Results are written to `accounts/`:

```
accounts/
├── accounts.json   # full structured result per account
├── accounts.csv    # spreadsheet-friendly summary
└── keys.txt        # email:api_key, one per line
```

## Usage

```bash
# Ten accounts with random mail.tm inboxes
python rewind_bulk.py -n 10

# Three accounts with a fixed password
python rewind_bulk.py -n 3 --password "MyFixedPassw0rd!"

# Custom API key label prefix
python rewind_bulk.py -n 5 --label-prefix worker

# Plan a batch without making any network calls
python rewind_bulk.py -n 3 --dry-run

# Keep going automatically when Rewind.ai rate limits your IP
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

### Options

| Flag | Description | Default |
| --- | --- | --- |
| `-n`, `--count` | Number of accounts to create | `1` |
| `--password` | Fixed password for every account | random |
| `--email` | Use one fixed email instead of mail.tm | generated |
| `--mail-domain` | mail.tm domain to build addresses from | first active |
| `--label-prefix` | Prefix for random API key names | `key` |
| `--output-dir` | Directory for result files | `accounts` |
| `--seed` | Seed the RNG for reproducible runs | random |
| `--delay` | Seconds between accounts | `1.0` |
| `--retries` | Retry attempts per account | `2` |
| `--skip-verification` | Create the key without verifying email | off |
| `--verify-timeout` | Seconds to wait for the verification email | `120` |
| `--poll-interval` | Seconds between inbox polls | `5` |
| `--wait-on-rate-limit` | Sleep and continue when rate limited | off |
| `--max-rate-limit-wait` | Cap for one rate-limit sleep (s) | `3600` |
| `--dry-run` | Plan only, no network calls | off |
| `-q`, `--quiet` | Suppress progress output | off |

## How it works

```
mail.tm  ──create inbox──▶  Rewind.ai /v1/auth/signup
                                    │
                          verification email ──▶ mail.tm inbox
                                    │
                     extract token ◀┘
                                    │
              Rewind.ai /v1/auth/verify-email  ──▶  verified
                                    │
              Rewind.ai /v1/api-keys  ──▶  sk-rewind-…
```

1. **Provision an inbox** on mail.tm.
2. **Sign up** at `POST /v1/auth/signup` with that address.
3. **Wait for the verification email** and pull the `token` out of the link.
4. **Verify** with `POST /v1/auth/verify-email`.
5. **Create an API key** with `POST /v1/api-keys`.

## Requirements

- Python 3.10 or newer
- `requests`
- Outbound network access to `api.mail.tm` and `api.rewind.ai`

## Project layout

```
rewind-bulk-creator/
├── rewind_bulk.py       # the whole CLI
├── requirements.txt
├── LICENSE
├── assets/
│   └── logo.svg
└── docs/
    ├── README.es.md
    ├── README.pt.md
    ├── README.de.md
    ├── README.ja.md
    └── README.zh.md
```

## Notes & limitations

- Rewind.ai limits signups per IP (for example 10 per hour). The tool detects
  the limit and either stops cleanly or waits, based on your flags.
- Verification email delivery depends on mail.tm; increase `--verify-timeout`
  on a slow day.
- Use responsibly. You are responsible for complying with the terms of service
  of any platform you automate.

## License

Released under the [MIT License](LICENSE).
