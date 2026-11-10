"""복지 길잡이 PoC — Rules as Code 판정 엔진 + 적응형 질문
- 판정은 3값 논리(True/False/None=미정)로 결정적으로 수행 → LLM 환각이 판정에 개입할 경로 없음
- 질문은 '아직 미정인 규칙을 가장 많이 확정시키는 변수'부터 묻는다 (탐욕적 선택)
⚠️ 규칙은 기초생활보장 4대 급여 '선정기준 소득'을 단순화한 예시. 재산 환산, 부양의무자 세부 기준 등은 생략.
"""
from dataclasses import dataclass
from typing import Callable

# 2026 기준중위소득 100% (원/월) — 출처: 보건복지부 고시 요약(2차 자료), 제출 전 원문 확인
MEDIAN_2026 = {1: 2_564_238, 2: 4_199_292, 3: 5_359_036, 4: 6_494_738, 5: 7_556_719, 6: 8_555_952}

VARS = {
    "household": "가구원 수는 몇 명인가요?",
    "income": "가구의 월 소득인정액은 얼마인가요?",
    "school_child": "초·중·고에 다니는 자녀가 있나요?",
    "obligor_ok": "부양의무자 기준을 충족하나요? (부양할 가족이 없거나 부양 능력이 없음)",
    "housing_cost": "월세·전세 등 주거비를 부담하고 있나요? (자가 수선 포함)",
}


def t(h, pct):
    return MEDIAN_2026[min(h, 6)] * pct


def AND(*xs):
    """3값 논리 AND: 하나라도 False면 False, 모두 True면 True, 그 외 None"""
    if any(x is False for x in xs):
        return False
    return True if all(x is True for x in xs) else None


def income_le(f, pct):
    if f.get("household") is None or f.get("income") is None:
        return None
    return f["income"] <= t(f["household"], pct)


def val(f, k):
    return f.get(k)


@dataclass
class Rule:
    name: str
    basis: str
    check: Callable[[dict], bool | None]
    needs: tuple


RULES = [
    Rule("생계급여", "소득인정액 ≤ 기준중위소득 32%", lambda f: income_le(f, 0.32), ("household", "income")),
    Rule("의료급여", "소득인정액 ≤ 40% + 부양의무자 기준",
         lambda f: AND(income_le(f, 0.40), val(f, "obligor_ok")), ("household", "income", "obligor_ok")),
    Rule("주거급여", "소득인정액 ≤ 48% + 주거비 부담",
         lambda f: AND(income_le(f, 0.48), val(f, "housing_cost")), ("household", "income", "housing_cost")),
    Rule("교육급여", "소득인정액 ≤ 50% + 초중고 자녀",
         lambda f: AND(income_le(f, 0.50), val(f, "school_child")), ("household", "income", "school_child")),
]


def decide(facts):
    return {r.name: r.check(facts) for r in RULES}


def explain(facts):
    out = []
    for r in RULES:
        d = r.check(facts)
        tag = {True: "해당", False: "비해당", None: "추가 정보 필요"}[d]
        out.append(f"{r.name}: {tag} (근거: {r.basis})")
    return out


def next_question(facts):
    """미정 규칙을 가장 많이 확정시킬 가능성이 큰 변수 선택 (미정 규칙들의 필요 변수 빈도)"""
    undecided = [r for r in RULES if r.check(facts) is None]
    if not undecided:
        return None
    count = {}
    for r in undecided:
        for v in r.needs:
            if v not in facts:
                count[v] = count.get(v, 0) + 1
    return max(count, key=count.get) if count else None


def run_adaptive(persona):
    facts, asked = {}, []
    while (q := next_question(facts)) is not None:
        facts[q] = persona[q]
        asked.append(q)
    return decide(facts), asked


def run_ask_all(persona):
    facts = {k: persona[k] for k in VARS}
    return decide(facts), list(VARS)


if __name__ == "__main__":
    demo = {"household": 1, "income": 3_000_000, "school_child": False, "obligor_ok": True, "housing_cost": True}
    res, asked = run_adaptive(demo)
    print("질문:", [VARS[a] for a in asked])
    print("\n".join(explain({k: demo[k] for k in asked})))
