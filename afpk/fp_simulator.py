"""AFPK 영플래너 챌린지 B안 - 재무진단 + 목표달성확률 시뮬레이터 (v2)
- 결정론: 상품별 세후 만기액 (금리 시나리오)
- 확률론: 주식 잔여분 몬테카를로 → 결혼자금 4,000만원 달성확률
가정값은 모두 ASSUMPTIONS에 모아 두었음. 제출 전 최신 기준으로 확인할 것.
"""
import numpy as np

ASSUMPTIONS = {
    "interest_tax": 0.154,      # 이자소득세(지방세 포함)
    "yfs_contrib": 0.06,        # 청년미래적금 일반형 정부기여금(우대형 0.12) [확인 필요]
    "stock_mu": 0.05,           # 국내주식 기대수익률(연) - 가정
    "stock_sigma": 0.20,        # 변동성(연) - 가정
    "goal": 4000,               # 결혼자금 목표(만원)
    "years": 3,
}

client = {
    "net_income": 300,
    "spend_before": {"월세": 60, "관리비·통신": 15, "식비": 55, "교통": 10, "여가·쇼핑": 40,
                     "보험": 10, "구독": 5, "학자금상환": 15, "경조사·기타": 10},
    "assets": {"입출금": 800, "정기예금": 1500, "국내주식": 700, "임차보증금": 1000},
    "debts": {"학자금대출": 600},
}
spend_after = dict(client["spend_before"], **{"여가·쇼핑": 32, "구독": 2, "식비": 50, "보험": 14})
alloc_after = {"청년미래적금": 50, "일반적금": 5, "연금저축": 25, "ISA(지수ETF)": 12}


def diagnose(spend, saving):
    inc, total = client["net_income"], sum(spend.values())
    a, d = sum(client["assets"].values()), sum(client["debts"].values())
    return {"총지출": total, "여력": inc - total, "저축률%": round(saving / inc * 100, 1),
            "주거비%": round((spend["월세"] + spend["관리비·통신"]) / inc * 100, 1),
            "비상자금(월)": round(client["assets"]["입출금"] / total, 1),
            "부채상환%": round(spend["학자금상환"] / inc * 100, 1), "순자산": a - d}


def installment(monthly, months, rate, tax=ASSUMPTIONS["interest_tax"]):
    """단리 적금 세후 만기액: 이자 = 월납입 × r/12 × n(n+1)/2"""
    interest = monthly * rate / 12 * months * (months + 1) / 2
    return monthly * months + interest * (1 - tax)


def youth_future(monthly, rate, contrib=ASSUMPTIONS["yfs_contrib"]):
    """청년미래적금 36개월: 비과세 + 정부기여금(이자 미부리로 보수적 가정)"""
    return installment(monthly, 36, rate, tax=0) + monthly * contrib * 36


def deposit(p, years, rate):
    for _ in range(years):
        p += p * rate * (1 - ASSUMPTIONS["interest_tax"])
    return p


def mc_goal_prob(safe_total, stock0=700, sell_ratio=0.43, n=100_000, seed=42):
    """주식 중 sell_ratio만 결혼자금에 투입. GBM으로 3년 후 가치 시뮬레이션"""
    rng = np.random.default_rng(seed)
    mu, s, T = ASSUMPTIONS["stock_mu"], ASSUMPTIONS["stock_sigma"], ASSUMPTIONS["years"]
    z = rng.standard_normal(n)
    st = stock0 * np.exp((mu - s**2 / 2) * T + s * np.sqrt(T) * z)
    total = safe_total + st * sell_ratio
    return (total >= ASSUMPTIONS["goal"]).mean(), np.percentile(total, [5, 50, 95])


if __name__ == "__main__":
    print("[현재]", diagnose(client["spend_before"], 50))
    print("[개선]", diagnose(spend_after, sum(alloc_after.values())))
    print("배분", sum(alloc_after.values()), "/ 여력", 300 - sum(spend_after.values()))
    print()
    for r in (0.025, 0.03, 0.035):
        old = installment(55, 12, r) * 3 + 0  # 비교용 근사(재예치 이자 무시)
        yfs = youth_future(50, r) + installment(5, 36, r)
        dep = deposit(1500, 3, r)
        safe = yfs + dep
        p, q = mc_goal_prob(safe)
        print(f"금리 {r*100:.1f}% | 청년미래적금+일반적금 {yfs:,.0f} | 예금 {dep:,.0f} | 안전자산 {safe:,.0f}"
              f" | 달성확률 {p*100:.1f}% | 5/50/95%ile {q.round(0)}")
    print()
    for c, name in ((0.06, "일반형"), (0.12, "우대형")):
        print(f"{name} 기여금 3년 합계: {50*c*36:,.0f}만원")
    print("연금저축 연 300만원 → 세액공제(16.5% 가정)", round(300 * 0.165, 1), "만원 [확인 필요]")
