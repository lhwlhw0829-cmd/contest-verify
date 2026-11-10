"""계산기 공식 검증: 닫힌 해(closed form) vs 월별 루프 시뮬레이션"""
import numpy as np
import pytest
from afpk.fp_simulator import installment, deposit, youth_future, mc_goal_prob, ASSUMPTIONS


def loop_installment(monthly, months, rate, tax):
    """독립 구현: k번째 납입금은 (months-k+1)개월 동안 단리 이자"""
    interest = sum(monthly * rate / 12 * (months - k) for k in range(months))
    return monthly * months + interest * (1 - tax)


@pytest.mark.parametrize("m,n,r,t", [(55, 12, 0.03, 0.154), (50, 36, 0.035, 0.0), (5, 36, 0.025, 0.154)])
def test_installment_closed_form_matches_loop(m, n, r, t):
    assert installment(m, n, r, tax=t) == pytest.approx(loop_installment(m, n, r, t))


def test_installment_interest_is_about_half_of_naive():
    """'원금총액×연이율'(AI가 흔히 하는 계산)은 12개월 적금 이자를 약 2배로 과대평가"""
    naive = 55 * 12 * 0.03
    correct = installment(55, 12, 0.03, tax=0) - 55 * 12
    assert naive / correct == pytest.approx(24 / 13, rel=1e-9)  # = 2n/(n+1)


def test_youth_future_components():
    r = 0.03
    v = youth_future(50, r, contrib=0.06)
    assert v == pytest.approx(installment(50, 36, r, tax=0) + 108)


def test_deposit_compound():
    assert deposit(1000, 1, 0.03) == pytest.approx(1000 * (1 + 0.03 * (1 - 0.154)))


def test_mc_converges():
    """시드 바꿔도 달성확률 차이가 작아야 함 (n=100,000 → 표준오차 약 0.1%p)"""
    ps = [mc_goal_prob(3795, seed=s)[0] for s in range(5)]
    assert max(ps) - min(ps) < 0.01
