#!/usr/bin/env python3
"""Operational verification script for AgentOS/Playground/Wish unification.

Verifies that unified API endpoints are accessible and responding correctly.
Exits with zero on success, non-zero on failure.
"""

import argparse
import os
import sys

try:
    import httpx
except ImportError:
    sys.exit(1)


class AgentOSVerifier:
    """Verifies AgentOS unified endpoints."""

    def __init__(self, api_base: str, api_key: str | None = None):
        self.api_base = api_base.rstrip("/")
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.checks_passed = 0
        self.checks_failed = 0

    def log(self, message: str, status: str = "INFO"):
        """Log a verification message."""
        {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
        }.get(status, "ℹ️")

    def check_endpoint(self, path: str, description: str) -> bool:
        """Check a single endpoint for accessibility.

        Args:
            path: API endpoint path (e.g., /api/v1/health)
            description: Human-readable description of the check

        Returns:
            bool: True if check passed, False otherwise
        """
        url = f"{self.api_base}{path}"
        try:
            self.log(f"Checking {description}: {url}", "INFO")
            response = httpx.get(url, headers=self.headers, timeout=10.0)
            response.raise_for_status()
            self.log(f"{description} is accessible (status: {response.status_code})", "SUCCESS")
            self.checks_passed += 1
            return True
        except httpx.ConnectError:
            self.log(f"Cannot connect to {description}: {url}", "ERROR")
            self.checks_failed += 1
            return False
        except httpx.HTTPStatusError as e:
            self.log(f"{description} returned error: {e.response.status_code} {e.response.reason_phrase}", "ERROR")
            self.checks_failed += 1
            return False
        except Exception as e:
            self.log(f"Unexpected error checking {description}: {e}", "ERROR")
            self.checks_failed += 1
            return False

    def verify_all(self) -> bool:
        """Run all verification checks.

        Returns:
            bool: True if all checks passed, False otherwise
        """
        self.log("Starting AgentOS unified API verification", "INFO")
        self.log(f"Target API: {self.api_base}", "INFO")

        # Check health endpoint
        self.check_endpoint("/api/v1/health", "Health endpoint")

        # Check AgentOS config endpoint
        self.check_endpoint("/api/v1/agentos/config", "AgentOS config endpoint")

        # Check wish catalog endpoint
        self.check_endpoint("/api/v1/wishes", "Wish catalog endpoint")

        # Check version endpoint
        self.check_endpoint("/api/v1/version", "Version endpoint")

        # Summary
        self.log("=" * 60, "INFO")
        self.log(f"Verification complete: {self.checks_passed} passed, {self.checks_failed} failed", "INFO")
        self.log("=" * 60, "INFO")

        if self.checks_failed == 0:
            self.log("All checks passed! Unified API is operational.", "SUCCESS")
            return True
        else:
            self.log(f"{self.checks_failed} check(s) failed. Review output above.", "ERROR")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify AgentOS unified API endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("HIVE_API_BASE", "http://localhost:8886"),
        help="API base URL (default: http://localhost:8886 or HIVE_API_BASE env var)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("HIVE_API_KEY"),
        help="API key for authentication (default: HIVE_API_KEY env var)",
    )

    args = parser.parse_args()

    verifier = AgentOSVerifier(api_base=args.api_base, api_key=args.api_key)
    success = verifier.verify_all()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
