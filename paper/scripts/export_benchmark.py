"""Export RSA-Auditor Bench manifest + PEMs from frozen backend fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.fixtures import FIXTURES  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "benchmark"
KEYS = OUT / "keys"


def _bitlen(n: int | None) -> int | None:
    if n is None:
        return None
    return int(n).bit_length()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    KEYS.mkdir(parents=True, exist_ok=True)

    entries = []
    for fx in FIXTURES:
        pem_name = f"{fx['id']}.pem"
        pem_path = KEYS / pem_name
        pem_path.write_text(fx["pem"], encoding="utf-8")
        n = int(fx["n"]) if fx.get("n") is not None else None
        e = fx.get("e")
        entries.append(
            {
                "id": fx["id"],
                "name": fx["name"],
                "bench_class": fx.get("bench_class") or fx.get("category"),
                "category": fx["category"],
                "expects_factor": bool(fx.get("expects_factor")),
                "expected_tier": fx.get("expected_tier"),
                "expected_method": fx.get("expected_method"),
                "expected_hint": fx.get("expected_hint"),
                "bitlength": _bitlen(n),
                "n": str(n) if n is not None else None,
                "e": str(e) if e is not None else None,
                "pem_file": f"keys/{pem_name}",
                "description": fx.get("description"),
            }
        )

    manifest = {
        "name": "RSA-Auditor Bench",
        "version": "1.0.0",
        "disclaimer": (
            "Synthetic labeled fixtures for auditor evaluation. "
            "INCONCLUSIVE/SUSPICIOUS ≠ SECURE. Not an Internet-scale corpus."
        ),
        "fixture_count": len(entries),
        "fixtures": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {OUT / 'manifest.json'} ({len(entries)} fixtures)")


if __name__ == "__main__":
    main()
