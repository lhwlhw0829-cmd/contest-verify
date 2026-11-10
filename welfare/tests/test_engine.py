from welfare.engine import AND, MEDIAN_2026, decide, run_adaptive, next_question


def test_three_valued_and():
    assert AND(True, None) is None
    assert AND(False, None) is False
    assert AND(True, True) is True


def test_boundary_is_inclusive():
    f = {"household": 1, "income": int(MEDIAN_2026[1] * 0.32), "obligor_ok": True,
         "housing_cost": True, "school_child": False}
    assert decide(f)["생계급여"] is True
    f["income"] += 1
    assert decide(f)["생계급여"] is False


def test_high_income_stops_after_two_questions():
    """소득이 50% 초과면 모든 급여가 확정 비해당 → 추가 질문 없이 종료"""
    p = {"household": 2, "income": 5_000_000, "school_child": True, "obligor_ok": True, "housing_cost": True}
    res, asked = run_adaptive(p)
    assert set(asked) == {"household", "income"}
    assert not any(res.values())


def test_never_asks_irrelevant():
    assert next_question({"household": 4, "income": 99_999_999}) is None
