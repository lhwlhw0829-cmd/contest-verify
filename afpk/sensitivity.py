"""가정값(주식 기대수익 μ, 변동성 σ, 투입 비율)에 대한 달성확률 민감도 분석 (금리 3.0% 기준)"""
from afpk import fp_simulator as fp

r = 0.03
safe = fp.youth_future(50, r) + fp.installment(5, 36, r) + fp.deposit(1500, 3, r)
print(f"안전자산(금리 3%): {safe:,.0f}만원\n")

print("μ \\ σ   " + "  ".join(f"{s:>6.0%}" for s in (0.15, 0.20, 0.25, 0.30)))
for mu in (-0.05, 0.0, 0.03, 0.05, 0.07):
    row = []
    for s in (0.15, 0.20, 0.25, 0.30):
        fp.ASSUMPTIONS.update(stock_mu=mu, stock_sigma=s)
        row.append(fp.mc_goal_prob(safe)[0])
    print(f"{mu:>6.0%}  " + "  ".join(f"{p:>6.1%}" for p in row))

fp.ASSUMPTIONS.update(stock_mu=0.05, stock_sigma=0.20)
print("\n주식 투입비율별 (μ=5%, σ=20%)")
for k in (0.3, 0.43, 0.6, 1.0):
    p, q = fp.mc_goal_prob(safe, sell_ratio=k)
    print(f"  {k:.0%}: 달성확률 {p:.1%}, 하위5% {q[0]:,.0f}")

print("\n우대형(12%) 적용 시")
safe12 = fp.youth_future(50, r, contrib=0.12) + fp.installment(5, 36, r) + fp.deposit(1500, 3, r)
print(f"  안전자산 {safe12:,.0f}만원, 달성확률 {fp.mc_goal_prob(safe12)[0]:.1%}")
