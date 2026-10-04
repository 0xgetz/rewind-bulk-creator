#!/usr/bin/env python3
"""
Rewind.ai Bulk Account Creator
==============================

Create multiple Rewind.ai accounts, auto-generate an API key for each one,
and export the results — optionally using disposable mail.tm inboxes.

This project is provided for educational and research purposes. You are
responsible for complying with the terms of service of any platform you use it
against.

Usage examples
--------------
    # Five accounts with random mail.tm inboxes
    python rewind_bulk.py --count 5

    # Ten accounts, keep only failed rows in the CSV
    python rewind_bulk.py -n 10

    # Use one fixed password for every account
    python rewind_bulk.py -n 3 --password "MyFixedPassw0rd!"

    # Dry run: build the plan and print it without touching any network
    python rewind_bulk.py -n 3 --dry-run

    # Custom key label prefix
    python rewind_bulk.py -n 5 --label-prefix worker

Outputs (written to the output directory, ``accounts/`` by default):
    accounts.json  — full structured result for every account
    accounts.csv   — spreadsheet friendly summary
    keys.txt       — one ``email:api_key`` pair per line, easy to pipe
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import secrets
import string
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

MAILTM_API = "https://api.mail.tm"
REWIND_API = "https://api.rewind.ai"

DEFAULT_TIMEOUT = 30
RANDOM_WORDS = [
    "falcon", "orbit", "cipher", "nimbus", "quantum", "vector", "lumen",
    "photon", "matrix", "nebula", "vertex", "pixel", "atlas", "zephyr",
    "ember", "glacier", "cinder", "sable", "raven", "onyx", "solstice",
    "aurora", "cobalt", "drift", "echo", "flux", "granite", "harbor",
    "ion", "jade", "krypton", "linen", "marlin", "north", "opal", "prism",
    "quartz", "rune", "steel", "titan", "umber", "vapor", "wisp", "xenon",
    "yarrow", "zircon",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

class RateLimitError(RuntimeError):
    """Raised when the upstream API reports a rate limit with a retry window."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class AccountResult:
    """One row of the final report."""

    index: int
    email: str | None = None
    password: str | None = None
    user_id: str | None = None
    plan: str | None = None
    verified: bool = False
    api_key_name: str | None = None
    api_key: str | None = None
    api_key_prefix: str | None = None
    status: str = "pending"
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def random_name(rng: random.Random) -> str:
    """Return a human-readable but unique random slug like ``cobalt-falcon-4f2a``."""
    word_a = rng.choice(RANDOM_WORDS)
    word_b = rng.choice(RANDOM_WORDS)
    suffix = secrets.token_hex(2)
    return f"{word_a}-{word_b}-{suffix}"


def random_username(rng: random.Random) -> str:
    """Return a mail.tm-safe username (alphanumeric only, <=16 chars)."""
    word_a = rng.choice(RANDOM_WORDS)
    word_b = rng.choice(RANDOM_WORDS)
    suffix = secrets.token_hex(2)
    username = f"{word_a}{word_b}{suffix}"
    while len(username) > 16:
        word_b = word_b[:-1]
        username = f"{word_a}{word_b}{suffix}"
    return username


def random_password(length: int = 16) -> str:
    """Return a strong random password that satisfies common strength rules."""
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*"
    all_chars = lowers + uppers + digits + symbols
    while True:
        pwd = "".join(secrets.choice(all_chars) for _ in range(length))
        if (
            any(c in lowers for c in pwd)
            and any(c in uppers for c in pwd)
            and any(c in digits for c in pwd)
            and any(c in symbols for c in pwd)
        ):
            return pwd


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, flush=True)


# --------------------------------------------------------------------------- #
# mail.tm
# --------------------------------------------------------------------------- #

class MailTmClient:
    """Tiny mail.tm API client used to provision disposable inboxes."""

    def __init__(
        self,
        session: requests.Session,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 5,
    ):
        self.session = session
        self.timeout = timeout
        self.max_retries = max_retries
        self._domain: str | None = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Perform a request, retrying with backoff on 429/5xx and empty bodies."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            resp = self.session.request(
                method,
                f"{MAILTM_API}{path}",
                json=json_body,
                headers=headers,
                timeout=self.timeout,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = resp.headers.get("Retry-After")
                try:
                    wait = float(retry_after) if retry_after else 2.0 * (attempt + 1)
                except ValueError:
                    wait = 2.0 * (attempt + 1)
                last_error = RuntimeError(
                    f"mail.tm {method} {path} -> {resp.status_code} (retrying in {wait:.0f}s)"
                )
                if attempt < self.max_retries:
                    time.sleep(min(wait, 30))
                    continue
                raise last_error
            if resp.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"mail.tm {method} {path} failed ({resp.status_code}): {resp.text[:200]}"
                )
            if not resp.content:
                return None
            try:
                return resp.json()
            except ValueError:
                return None
        raise last_error or RuntimeError("mail.tm request failed")

    def domain(self) -> str:
        if self._domain:
            return self._domain
        data = self._request("GET", "/domains")
        members = data if isinstance(data, list) else (data or {}).get("hydra:member", [])
        active = [d for d in members if isinstance(d, dict) and d.get("isActive")]
        if not active:
            raise RuntimeError("mail.tm returned no active domains")
        self._domain = active[0]["domain"]
        return self._domain

    def create_account(self, address: str, password: str) -> dict[str, Any]:
        data = self._request(
            "POST", "/accounts", json_body={"address": address, "password": password}
        )
        return data or {}

    def inbox_for(self, address: str, password: str) -> str:
        """Provision a fresh inbox and return its address."""
        self.create_account(address, password)
        return address

    def token(self, address: str, password: str) -> str:
        data = self._request(
            "POST", "/token", json_body={"address": address, "password": password}
        )
        if not data or "token" not in data:
            raise RuntimeError("mail.tm returned no auth token")
        return data["token"]

    def messages(self, auth_token: str) -> list[dict[str, Any]]:
        data = self._request(
            "GET", "/messages", headers={"Authorization": f"Bearer {auth_token}"}
        )
        if isinstance(data, list):
            return [m for m in data if isinstance(m, dict)]
        if isinstance(data, dict):
            return [m for m in data.get("hydra:member", []) if isinstance(m, dict)]
        return []

    def message_body(self, auth_token: str, message_id: str) -> str:
        """Return the plain-text + html body of one message as a single string."""
        data = self._request(
            "GET",
            f"/messages/{message_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        if not isinstance(data, dict):
            return ""
        parts: list[str] = []
        for field in ("text", "html", "intro"):
            value = data.get(field)
            if isinstance(value, list):
                parts.extend(str(v) for v in value)
            elif value:
                parts.append(str(value))
        return "\n".join(parts)

    def wait_for_verification_token(
        self,
        address: str,
        password: str,
        poll_interval: float = 5.0,
        max_wait: float = 120.0,
    ) -> str:
        """Poll the inbox until the Rewind verification link shows up.

        Returns the token embedded in ``/auth/verify-email?token=...``.
        """
        auth_token = self.token(address, password)
        deadline = time.monotonic() + max_wait
        pattern = re.compile(r"verify-email\?token=([0-9a-f]{16,})", re.IGNORECASE)
        while time.monotonic() < deadline:
            for msg in self.messages(auth_token):
                body = self.message_body(auth_token, msg["id"])
                match = pattern.search(body)
                if match:
                    return match.group(1)
            time.sleep(poll_interval)
        raise TimeoutError(
            f"no verification email for {address} within {max_wait:.0f}s"
        )


# --------------------------------------------------------------------------- #
# Rewind.ai
# --------------------------------------------------------------------------- #

class RewindClient:
    """Minimal Rewind.ai client covering signup and API key creation."""

    def __init__(
        self,
        session: requests.Session,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 4,
    ):
        self.session = session
        self.timeout = timeout
        self.max_retries = max_retries
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Origin": "https://rewind.ai",
                "Referer": "https://rewind.ai/signup/",
            }
        )

    def _post(self, path: str, *, json_body: dict[str, Any], token: str | None = None) -> requests.Response:
        """POST with backoff on transient 429/5xx responses."""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        last: requests.Response | None = None
        for attempt in range(self.max_retries + 1):
            resp = self.session.post(
                f"{REWIND_API}{path}", json=json_body, headers=headers, timeout=self.timeout
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                last = resp
                if attempt < self.max_retries:
                    time.sleep(min(3.0 * (attempt + 1), 20))
                    continue
            return resp
        assert last is not None
        return last

    def signup(self, email: str, password: str) -> dict[str, Any]:
        resp = self._post(
            "/v1/auth/signup", json_body={"email": email, "password": password}
        )
        if resp.status_code == 429:
            retry_after = None
            try:
                details = resp.json().get("error", {}).get("details", {})
                retry_after = details.get("retryAfterSeconds")
            except ValueError:
                pass
            raise RateLimitError(
                f"signup rate limited by Rewind.ai ({resp.text[:160]})", retry_after
            )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"signup failed ({resp.status_code}): {resp.text[:200]}"
            )
        return resp.json()

    def verify_email(self, access_token: str, token: str) -> None:
        resp = self._post(
            "/v1/auth/verify-email", json_body={"token": token}, token=access_token
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"email verification failed ({resp.status_code}): {resp.text[:200]}"
            )

    def me(self, access_token: str) -> dict[str, Any]:
        resp = self.session.get(
            f"{REWIND_API}/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def resend_verification(self, access_token: str) -> None:
        self._post("/v1/auth/resend-verification", json_body={}, token=access_token)

    def create_api_key(self, access_token: str, name: str) -> dict[str, Any]:
        resp = self._post(
            "/v1/api-keys", json_body={"name": name}, token=access_token
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"api key creation failed ({resp.status_code}): {resp.text[:200]}"
            )
        return resp.json()


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def create_one(
    index: int,
    args: argparse.Namespace,
    rng: random.Random,
    session: requests.Session,
) -> AccountResult:
    """Create a single account + API key and return the result row."""
    result = AccountResult(index=index)

    try:
        # 1. Build an identity ------------------------------------------------
        slug = random_username(rng)
        password = args.password or random_password()
        mail = MailTmClient(session)
        if args.email:
            email = args.email
        else:
            domain = args.mail_domain or mail.domain()
            email = f"{slug}@{domain}"
            if not args.dry_run:
                mail.create_account(email, password)

        result.email = email
        result.password = password

        if args.dry_run:
            result.status = "dry-run"
            result.api_key_name = f"{args.label_prefix}-{random_name(rng)}"
            return result

        # 2. Sign up ----------------------------------------------------------
        rewind = RewindClient(session)
        auth = rewind.signup(email, password)
        access_token = auth.get("accessToken")
        result.user_id = (auth.get("user") or {}).get("id")
        result.plan = (auth.get("user") or {}).get("plan")
        if not access_token:
            raise RuntimeError("signup response contained no access token")

        # 3. Verify the email via the mail.tm inbox ---------------------------
        if not args.skip_verification:
            token = mail.wait_for_verification_token(
                email,
                password,
                poll_interval=args.poll_interval,
                max_wait=args.verify_timeout,
            )
            rewind.verify_email(access_token, token)
            user = rewind.me(access_token)
            result.verified = bool(user.get("emailVerifiedAt"))
            if not result.verified:
                raise RuntimeError("verification did not stick (emailVerifiedAt is null)")

        # 4. Create an API key -------------------------------------------------
        key_name = f"{args.label_prefix}-{random_name(rng)}"
        key_data = rewind.create_api_key(access_token, key_name)
        result.api_key_name = key_name
        result.api_key = key_data.get("key")
        result.api_key_prefix = key_data.get("keyPrefix")
        result.status = "success"
        return result

    except RateLimitError:
        raise
    except Exception as exc:  # noqa: BLE001 - report and continue
        result.status = "failed"
        result.error = str(exc)
        return result


def write_outputs(results: list[AccountResult], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "accounts.json"
    json_path.write_text(
        json.dumps([r.to_row() for r in results], indent=2), encoding="utf-8"
    )

    csv_path = out_dir / "accounts.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0].to_row().keys()))
        writer.writeheader()
        for row in results:
            writer.writerow(row.to_row())

    keys_path = out_dir / "keys.txt"
    with keys_path.open("w", encoding="utf-8") as fh:
        for row in results:
            if row.api_key:
                fh.write(f"{row.email}:{row.api_key}\n")


def positive_int(value: str) -> int:
    try:
        ivalue = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not an integer") from exc
    if ivalue < 1:
        raise argparse.ArgumentTypeError("count must be >= 1")
    return ivalue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rewind_bulk",
        description="Bulk-create Rewind.ai accounts and auto-generate API keys.",
    )
    parser.add_argument(
        "-n", "--count", type=positive_int, default=1,
        help="number of accounts to create (default: 1)",
    )
    parser.add_argument("--password", help="fixed password for every account")
    parser.add_argument(
        "--email", help="use one fixed email instead of generating mail.tm inboxes"
    )
    parser.add_argument(
        "--mail-domain",
        help="mail.tm domain to build addresses from (default: first active domain)",
    )
    parser.add_argument(
        "--label-prefix", default="key",
        help="prefix for the random API key name (default: key)",
    )
    parser.add_argument(
        "--output-dir", default="accounts",
        help="directory for result files (default: accounts)",
    )
    parser.add_argument(
        "--seed", type=int, help="seed the RNG for reproducible runs"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="seconds to sleep between accounts (default: 1.0)",
    )
    parser.add_argument(
        "--retries", type=int, default=2,
        help="retry attempts per account on failure (default: 2)",
    )
    parser.add_argument(
        "--skip-verification", action="store_true",
        help="sign up and create a key without clicking the email verification link",
    )
    parser.add_argument(
        "--verify-timeout", type=float, default=120.0,
        help="seconds to wait for the verification email (default: 120)",
    )
    parser.add_argument(
        "--poll-interval", type=float, default=5.0,
        help="seconds between inbox polls (default: 5)",
    )
    parser.add_argument(
        "--wait-on-rate-limit", action="store_true",
        help="sleep when Rewind.ai rate limits this IP instead of stopping",
    )
    parser.add_argument(
        "--max-rate-limit-wait", type=float, default=3600.0,
        help="cap for a single rate-limit sleep in seconds (default: 3600)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="plan the run without making network calls",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="suppress progress output"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.email and args.count > 1:
        parser.error("--email cannot be combined with a count greater than 1")

    rng = random.Random(args.seed)
    session = requests.Session()
    results: list[AccountResult] = []

    log(f"Creating {args.count} account(s)...", args.quiet)

    for i in range(1, args.count + 1):
        attempt = 0
        result: AccountResult | None = None
        while attempt <= args.retries:
            try:
                result = create_one(i, args, rng, session)
            except RateLimitError as exc:
                retry_after = exc.retry_after or 3600
                log(
                    f"  [{i}] rate limited by Rewind.ai — retry after "
                    f"{retry_after:.0f}s ({exc})",
                    args.quiet,
                )
                if not args.wait_on_rate_limit:
                    log(
                        "  Stopping remaining accounts. Re-run later, or pass "
                        "--wait-on-rate-limit to sleep and continue.",
                        args.quiet,
                    )
                    skipped = AccountResult(index=i, status="skipped", error="rate limited")
                    results.append(skipped)
                    write_outputs(results, Path(args.output_dir))
                    failed = sum(1 for r in results if r.status == "failed")
                    return 0 if failed == 0 else 1
                wait = min(retry_after, args.max_rate_limit_wait)
                log(f"  Sleeping {wait:.0f}s before retrying...", args.quiet)
                time.sleep(wait)
                continue
            if result.status in ("success", "dry-run") or attempt == args.retries:
                break
            attempt += 1
            log(
                f"  [{i}] retry {attempt}/{args.retries} after error: {result.error}",
                args.quiet,
            )
            time.sleep(args.delay)
        assert result is not None
        results.append(result)

        if result.status == "success":
            log(
                f"  [{i}] OK  {result.email}  ->  {result.api_key}", args.quiet
            )
        elif result.status == "dry-run":
            log(
                f"  [{i}] dry-run  email={result.email}  label={result.api_key_name}",
                args.quiet,
            )
        else:
            log(f"  [{i}] FAIL  {result.email}  ({result.error})", args.quiet)

        if i < args.count and args.delay:
            time.sleep(args.delay)

    out_dir = Path(args.output_dir)
    write_outputs(results, out_dir)

    ok = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "failed")
    log(
        f"\nDone. success={ok} failed={failed} -> {out_dir}/"
        f" (accounts.json, accounts.csv, keys.txt)",
        args.quiet,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
