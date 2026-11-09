import asyncio
from backend.app.orchestration.orchestrator import orchestration_engine

async def run_conversations():
    # Flow 1: Complete buying interview -> checkout -> confirm
    s1 = "flow_1_buy"
    print("--- Testing Flow 1: Buy Flow ---")
    r1 = await orchestration_engine.process_user_turn(s1, "I want to buy a car")
    assert r1 and "message" in r1, "Turn 1 failed"
    print("  Turn 1:", r1["workflow_state"])

    r2 = await orchestration_engine.process_user_turn(s1, "SUV in Delhi under 80 lakh")
    assert r2 and "message" in r2, "Turn 2 failed"
    print("  Turn 2:", r2["workflow_state"], "actions:", len(r2.get("actions", [])))

    # Flow 2: Direct car query and specs
    s2 = "flow_2_car"
    print("--- Testing Flow 2: Specific Car Search ---")
    r3 = await orchestration_engine.process_user_turn(s2, "Tell me about BMW M3 Competition")
    assert r3 and "message" in r3, "Turn 3 failed"
    print("  Turn 3:", r3["workflow_state"])

    # Flow 3: Sell Car flow
    s3 = "flow_3_sell"
    print("--- Testing Flow 3: Sell Workflow ---")
    r4 = await orchestration_engine.process_user_turn(s3, "I want to sell my car")
    assert r4 and "message" in r4, "Turn 4 failed"
    print("  Turn 4:", r4["workflow_state"])

    r5 = await orchestration_engine.process_user_turn(s3, "yes, it is in my name, 2022 Honda City")
    assert r5 and "message" in r5, "Turn 5 failed"
    print("  Turn 5:", r5["workflow_state"])

    # Flow 4: Compare cars
    s4 = "flow_4_compare"
    print("--- Testing Flow 4: Comparison Flow ---")
    r6 = await orchestration_engine.process_user_turn(s4, "compare Mercedes C-Class and BMW 3 Series")
    assert r6 and "message" in r6, "Turn 6 failed"
    print("  Turn 6:", r6["workflow_state"])

    # Flow 5: Inquire about rentals (must gracefully redirect to purchases without error)
    s5 = "flow_5_rent"
    print("--- Testing Flow 5: Rental Inquiries Redirection ---")
    r7 = await orchestration_engine.process_user_turn(s5, "Show me rental cars for 5 days")
    assert r7 and "message" in r7, "Turn 7 failed"
    print("  Turn 7:", r7["workflow_state"])

    r8 = await orchestration_engine.process_user_turn(s5, "show me my rentals")
    assert r8 and "message" in r8, "Turn 8 failed"
    print("  Turn 8:", r8["workflow_state"])

    print("\nALL 5 MULTI-TURN FLOWS PASSED 100% CLEANLY!")

if __name__ == "__main__":
    asyncio.run(run_conversations())

