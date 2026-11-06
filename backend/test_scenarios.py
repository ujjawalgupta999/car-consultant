import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.orchestration.orchestrator import orchestration_engine
from app.repositories.session import session_repo
from app.agents.intent_detector import intent_detector

@pytest.mark.asyncio
async def test_scenarios():
    sess = session_repo.get_or_create_session("test_sess_scenarios")

    # Scenario 1: User says "i want to buy an car sedan"
    r1 = await orchestration_engine.process_user_turn(sess.session_id, "i want to buy an car sedan")
    actions1 = [a["type"] for a in r1.get("website_actions", [])]
    paths1 = [a.get("payload", {}).get("path") for a in r1.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "NAVIGATE_TO_PAGE" in actions1 or "NAVIGATE" in actions1
    assert "/buy" in paths1
    assert len(r1.get("cards", [])) > 0
    print("\n[PASS] Scenario 1: Buy sedan navigates to /buy with cards")

    # Scenario 2: Comparison query
    r2 = await orchestration_engine.process_user_turn(
        sess.session_id,
        "Please provide an objective, expert comparison between: Tata Harrier Fearless Plus (2024) vs Toyota Fortuner Legender (2024)."
    )
    actions2 = [a["type"] for a in r2.get("website_actions", [])]
    paths2 = [a.get("payload", {}).get("path") for a in r2.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "ADD_TO_COMPARISON" in actions2
    assert "/compare" in paths2
    assert "Benchmark Analysis" in r2["message"]["content"]
    print("[PASS] Scenario 2: Comparison navigates to /compare with side-by-side analysis")

    # Scenario 3: Negation "i want to but an sedan instead of suv"
    r3 = await orchestration_engine.process_user_turn(sess.session_id, "i want to but an sedan instead of suv")
    paths3 = [a.get("payload", {}).get("path") for a in r3.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/buy" in paths3
    assert r3["preferences"]["category"] == "Sedan"
    print("[PASS] Scenario 3: 'sedan instead of suv' correctly selects Sedan")

    # Scenario A: "Show me the list of my cars"
    r_a = await orchestration_engine.process_user_turn(sess.session_id, "Show me the list of my cars")
    paths_a = [a.get("payload", {}).get("path") for a in r_a.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/dashboard/vehicles" in paths_a
    assert len(r_a.get("cards", [])) > 0
    print("[PASS] Scenario A: Show me my cars opens /dashboard/vehicles")

    # Scenario B: "Show me all the cars I have purchased"
    r_b = await orchestration_engine.process_user_turn(sess.session_id, "Show me all the cars I have purchased")
    paths_b = [a.get("payload", {}).get("path") for a in r_b.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/dashboard/purchases" in paths_b
    assert len(r_b.get("cards", [])) > 0
    print("[PASS] Scenario B: Show my purchases opens /dashboard/purchases")

    # Scenario C: "Show my rental history"
    r_c = await orchestration_engine.process_user_turn(sess.session_id, "Show my rental history")
    paths_c = [a.get("payload", {}).get("path") for a in r_c.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/dashboard/rentals" in paths_c
    assert len(r_c.get("cards", [])) > 0
    print("[PASS] Scenario C: Show my rental history opens /dashboard/rentals")

    # Scenario D: "I want to sell my sedan" followed by "Yes" / "Okay, continue"
    r_d1 = await orchestration_engine.process_user_turn(sess.session_id, "I want to sell my sedan")
    paths_d1 = [a.get("payload", {}).get("path") for a in r_d1.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/sell-car" in paths_d1
    assert "registered in your name" in r_d1["message"]["content"].lower()

    # Affirmative response
    r_d2 = await orchestration_engine.process_user_turn(sess.session_id, "Okay, continue")
    assert "/sell-car" in [a.get("payload", {}).get("path") for a in r_d2.get("website_actions", []) if "path" in a.get("payload", {})]
    assert any(a["type"] == "PREFILL_SELL_FORM" for a in r_d2.get("website_actions", []))
    assert "registered in your name" not in r_d2["message"]["content"].lower()
    print("[PASS] Scenario D: Sell workflow handles affirmative reply and prefills sell form without loop")

    # Scenario G: "Show my previous payments"
    r_g = await orchestration_engine.process_user_turn(sess.session_id, "Show my previous payments")
    paths_g = [a.get("payload", {}).get("path") for a in r_g.get("website_actions", []) if "path" in a.get("payload", {})]
    assert "/dashboard/payments" in paths_g
    assert len(r_g.get("cards", [])) > 0
    print("[PASS] Scenario G: Show my previous payments opens /dashboard/payments")

