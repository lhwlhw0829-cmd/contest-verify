"""가상 페르소나 N명으로 적응형 질문 vs 전체 질문 비교
지표: 판정 일치율(정답 = 모든 정보로 판정), 평균 질문 수, 미정 판정 비율
"""
import random
import statistics as st
from welfare.engine import MEDIAN_2026, VARS, decide, run_adaptive, run_ask_all

random.seed(0)


def make_persona():
    h = random.choices([1, 2, 3, 4, 5], weights=[35, 28, 17, 15, 5])[0]
    # 소득: 중위소득 대비 비율을 0~150%에서 샘플 (저소득층 과대표집해 경계 사례 확보)
    ratio = random.choice([random.uniform(0, 0.6), random.uniform(0, 1.5)])
    return {
        "household": h,
        "income": int(MEDIAN_2026[h] * ratio),
        "school_child": h >= 2 and random.random() < 0.45,
        "obligor_ok": random.random() < 0.7,
        "housing_cost": random.random() < 0.75,
    }


def main(n=1000):
    P = [make_persona() for _ in range(n)]
    agree, q_ad, q_all, undecided = 0, [], [], 0
    for p in P:
        gold = decide(p)
        ad, asked = run_adaptive(p)
        al, asked_all = run_ask_all(p)
        assert al == gold
        agree += ad == gold
        undecided += any(v is None for v in ad.values())
        q_ad.append(len(asked))
        q_all.append(len(asked_all))
    print(f"페르소나 {n}명")
    print(f"판정 일치율(적응형 vs 정답): {agree / n:.1%}")
    print(f"미정으로 끝난 비율: {undecided / n:.1%}")
    print(f"평균 질문 수: 적응형 {st.mean(q_ad):.2f} vs 전체 {st.mean(q_all):.2f} "
          f"(감소 {1 - st.mean(q_ad) / st.mean(q_all):.1%})")
    dist = {k: q_ad.count(k) for k in sorted(set(q_ad))}
    print("질문 수 분포:", dist)
    elig = {name: sum(decide(p)[name] for p in P) for name in decide(P[0])}
    print("급여별 해당자 수:", elig)


if __name__ == "__main__":
    main()
