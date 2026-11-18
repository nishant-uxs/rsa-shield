from app.crypto.pollard_p1 import pollard_p1


def test_pollard_p1_recovers_smooth_factor():
    # 641 | F5 and 641-1 = 640 is highly smooth
    n = 641 * 6700417
    r = pollard_p1(n, B1=1000, timeout_ms=3000)
    assert r.factor_found is True
    assert r.factor in {641, 6700417}
    assert n % r.factor == 0
