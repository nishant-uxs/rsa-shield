"""Subquadratic Batch GCD using Bernstein's Product and Remainder Tree algorithm.

Theoretical basis:
- D.J. Bernstein, "How to find small factors of integers" (2004)
- Nadia Heninger et al., "Mining Your Ps and Qs: Detection of Widespread Weak Keys
  in Network Devices", USENIX Security 2012.

Replaces naive pairwise O(N^2) GCD checks with subquadratic O(N log^2 N) product-tree
and remainder-tree reductions, scaling from dozens of lab keys to thousands of
infrastructure keys in seconds.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from math import gcd
from typing import Any


@dataclass
class SharedFactorHit:
    i: int
    j: int
    factor: int
    key_id_a: str
    key_id_b: str


@dataclass
class BatchGcdResult:
    moduli_count: int
    pairs_checked: int
    hits: list[SharedFactorHit]
    message: str
    algorithm: str = "Bernstein Subquadratic Product/Remainder Tree"
    elapsed_ms: float = 0.0


def build_product_tree(moduli: list[int]) -> list[list[int]]:
    """Build a binary product tree upwards from leaves.
    
    Level 0 contains the original moduli.
    Level k contains products of pairs from Level k-1.
    """
    if not moduli:
        return [[]]
    tree: list[list[int]] = [list(moduli)]
    while len(tree[-1]) > 1:
        current = tree[-1]
        next_level: list[int] = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                next_level.append(current[i] * current[i + 1])
            else:
                next_level.append(current[i])
        tree.append(next_level)
    return tree


def build_remainder_tree(tree: list[list[int]], moduli: list[int]) -> list[int]:
    """Compute R_i = (Product of all m_j) mod m_i^2 top-down.
    
    Using the algebraic property: if A and B are child nodes of C = A * B,
    then (P mod C^2) mod A^2 = P mod A^2.
    """
    n = len(moduli)
    if n == 0:
        return []
    if n == 1:
        return [0]
    if len(tree) < 2:
        return [0] * n

    remainders: list[list[int] | None] = [None] * len(tree)
    top = tree[-2]
    if len(top) == 2:
        a, b = top[0], top[1]
        remainders[-2] = [a * (b % a), b * (a % b)]
    else:
        remainders[-2] = [0]

    for k in range(len(tree) - 3, -1, -1):
        prev_r = remainders[k + 1]
        assert prev_r is not None
        curr_nodes = tree[k]
        curr_r: list[int] = []
        for i, node in enumerate(curr_nodes):
            parent_val = prev_r[i // 2]
            node_sq = node * node
            curr_r.append(parent_val % node_sq if node_sq > 0 else 0)
        remainders[k] = curr_r

    leaf_r = remainders[0]
    return leaf_r if leaf_r is not None else [0] * n


def fast_batch_gcd(
    moduli: list[int],
    key_ids: list[str] | None = None,
) -> BatchGcdResult:
    """Execute subquadratic O(N log^2 N) Batch-GCD across moduli using Bernstein's tree."""
    t0 = time.perf_counter()
    n = len(moduli)
    if key_ids is None:
        key_ids = [str(i) for i in range(n)]
    if len(moduli) != len(key_ids):
        raise ValueError("moduli and key_ids length mismatch")

    pairs = n * (n - 1) // 2
    if n <= 1:
        elapsed = (time.perf_counter() - t0) * 1000
        return BatchGcdResult(
            moduli_count=n,
            pairs_checked=pairs,
            hits=[],
            message="Batch GCD: minimum 2 moduli required for collision scan.",
            algorithm="Bernstein Subquadratic Product/Remainder Tree",
            elapsed_ms=round(elapsed, 2),
        )

    # Filter out trivial moduli (<= 1) while preserving index mapping
    valid_indices = [i for i, m in enumerate(moduli) if m > 1]
    if len(valid_indices) <= 1:
        elapsed = (time.perf_counter() - t0) * 1000
        return BatchGcdResult(
            moduli_count=n,
            pairs_checked=pairs,
            hits=[],
            message="Batch GCD: insufficient valid moduli (> 1).",
            algorithm="Bernstein Subquadratic Product/Remainder Tree",
            elapsed_ms=round(elapsed, 2),
        )

    clean_moduli = [moduli[i] for i in valid_indices]
    tree = build_product_tree(clean_moduli)
    leaf_remainders = build_remainder_tree(tree, clean_moduli)

    # Identify individual keys that have shared factors with any other key
    vulnerable_indices: list[int] = []
    for local_idx, m in enumerate(clean_moduli):
        rem = leaf_remainders[local_idx]
        z = rem // m
        g = gcd(m, z)
        if 1 < g < m:
            vulnerable_indices.append(valid_indices[local_idx])

    # Pairwise match ONLY the flagged vulnerable keys to populate collision records
    hits: list[SharedFactorHit] = []
    v_len = len(vulnerable_indices)
    for idx_a in range(v_len):
        i = vulnerable_indices[idx_a]
        for idx_b in range(idx_a + 1, v_len):
            j = vulnerable_indices[idx_b]
            g = gcd(moduli[i], moduli[j])
            if 1 < g < moduli[i] and g < moduli[j]:
                hits.append(
                    SharedFactorHit(
                        i=i,
                        j=j,
                        factor=g,
                        key_id_a=key_ids[i],
                        key_id_b=key_ids[j],
                    )
                )

    elapsed = (time.perf_counter() - t0) * 1000
    if not hits:
        msg = (
            f"Batch GCD [Subquadratic Tree]: checked {n} moduli ({pairs} pairwise equivalents) "
            f"in {elapsed:.2f} ms — no shared prime factors. "
            "Absence of shared factors is not a security proof for any single key."
        )
    else:
        msg = (
            f"Batch GCD [Subquadratic Tree]: {len(hits)} shared-factor collision(s) detected among {n} moduli "
            f"in {elapsed:.2f} ms. Shared primes imply immediate factorization of involved keys."
        )

    return BatchGcdResult(
        moduli_count=n,
        pairs_checked=pairs,
        hits=hits,
        message=msg,
        algorithm="Bernstein Subquadratic Product/Remainder Tree",
        elapsed_ms=round(elapsed, 2),
    )


def naive_batch_gcd(
    moduli: list[int],
    key_ids: list[str] | None = None,
) -> BatchGcdResult:
    """Legacy naive pairwise O(N^2) GCD check (for ablation & benchmarking)."""
    t0 = time.perf_counter()
    n = len(moduli)
    if key_ids is None:
        key_ids = [str(i) for i in range(n)]
    if len(moduli) != len(key_ids):
        raise ValueError("moduli and key_ids length mismatch")

    hits: list[SharedFactorHit] = []
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            a, b = moduli[i], moduli[j]
            if a <= 1 or b <= 1:
                continue
            g = gcd(a, b)
            if 1 < g < a and g < b:
                hits.append(
                    SharedFactorHit(
                        i=i,
                        j=j,
                        factor=g,
                        key_id_a=key_ids[i],
                        key_id_b=key_ids[j],
                    )
                )

    elapsed = (time.perf_counter() - t0) * 1000
    if not hits:
        msg = (
            f"Batch GCD [Pairwise O(N^2)]: checked {pairs} pairs across {n} moduli in {elapsed:.2f} ms — "
            "no shared prime factors."
        )
    else:
        msg = (
            f"Batch GCD [Pairwise O(N^2)]: {len(hits)} shared-factor collision(s) among {n} moduli "
            f"({pairs} pairs) in {elapsed:.2f} ms."
        )
    return BatchGcdResult(
        moduli_count=n,
        pairs_checked=pairs,
        hits=hits,
        message=msg,
        algorithm="Naive Pairwise O(N^2)",
        elapsed_ms=round(elapsed, 2),
    )


def batch_gcd(
    moduli: list[int],
    key_ids: list[str] | None = None,
    *,
    method: str = "subquadratic",
) -> BatchGcdResult:
    """Unified entry point for Batch GCD.
    
    Defaults to subquadratic Bernstein tree, with optional pairwise mode for baseline comparison.
    """
    if method == "naive" or method == "pairwise":
        return naive_batch_gcd(moduli, key_ids)
    return fast_batch_gcd(moduli, key_ids)


def benchmark_batch_gcd_scaling(sizes: list[int] | None = None) -> list[dict[str, Any]]:
    """Generate empirical comparative scaling benchmark for research paper evaluation."""
    from Crypto.Util.number import getPrime

    if sizes is None:
        sizes = [20, 50, 100, 200, 400]

    # Shared prime collision fixture
    shared_p = getPrime(256)
    results: list[dict[str, Any]] = []

    for n in sizes:
        # Construct synthetic moduli corpus where key 0 and key 1 share prime p
        corpus = [shared_p * getPrime(256), shared_p * getPrime(256)]
        for _ in range(n - 2):
            corpus.append(getPrime(256) * getPrime(256))

        # 1. Benchmark Naive Pairwise
        t0 = time.perf_counter()
        naive_res = naive_batch_gcd(corpus)
        t_naive_ms = (time.perf_counter() - t0) * 1000

        # 2. Benchmark Subquadratic Bernstein Tree
        t0 = time.perf_counter()
        fast_res = fast_batch_gcd(corpus)
        t_fast_ms = (time.perf_counter() - t0) * 1000

        speedup = t_naive_ms / t_fast_ms if t_fast_ms > 0 else 1.0

        results.append({
            "key_count": n,
            "pairs_equivalent": n * (n - 1) // 2,
            "naive_pairwise_ms": round(t_naive_ms, 2),
            "subquadratic_tree_ms": round(t_fast_ms, 2),
            "speedup_factor": f"{speedup:.2f}x",
            "hits_detected": len(fast_res.hits),
            "parity_verified": len(naive_res.hits) == len(fast_res.hits),
        })

    return results
