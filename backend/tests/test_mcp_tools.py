import pytest
from backend.app.mcp.server import list_mcp_tools, call_mcp_tool

def test_list_all_ten_mcp_tools():
    tools = list_mcp_tools()
    assert len(tools) == 10
    names = {t["name"] for t in tools}
    expected = {
        "search_vehicles",
        "get_vehicle_details",
        "check_vehicle_availability",
        "compare_vehicles",
        "calculate_booking_total",
        "create_booking",
        "create_purchase_order",
        "get_booking_status",
        "simulate_mock_payment",
        "get_order_confirmation"
    }
    assert names == expected

def test_mcp_search_and_details():
    res = call_mcp_tool("search_vehicles", {
        "intent": "rent",
        "location": "Delhi",
        "category": "SUV",
        "max_price": 3000.0,
        "transmission": "automatic"
    })
    assert res["status"] == "success"
    assert res["count"] > 0
    vehicle_id = res["vehicles"][0]["id"]

    details = call_mcp_tool("get_vehicle_details", {"vehicle_id": vehicle_id})
    assert details["status"] == "success"
    assert details["vehicle"]["id"] == vehicle_id

def test_mcp_calculate_and_create_booking_and_payment():
    # 1. Calculate price
    calc = call_mcp_tool("calculate_booking_total", {
        "vehicle_id": "CAR-001",
        "duration_days": 5,
        "addon_ids": ["addon_insurance_zero_dep"]
    })
    assert calc["status"] == "success"
    total_amount = calc["pricing"]["total_amount"]
    assert total_amount > 0

    # 2. Create booking
    booking_res = call_mcp_tool("create_booking", {
        "session_id": "sess_test_123",
        "vehicle_id": "CAR-001",
        "customer_name": "Rohan Sharma",
        "customer_email": "rohan@example.com",
        "customer_phone": "+91 98765 43210",
        "driver_license_number": "DL-1420110012345",
        "pickup_date": "2026-12-15",
        "return_date": "2026-12-20",
        "duration_days": 5,
        "pickup_location": "Delhi Airport T3",
        "return_location": "Delhi Airport T3",
        "addon_ids": ["addon_insurance_zero_dep"],
        "idempotency_key": "idemp_test_mcp_bk_1"
    })
    assert booking_res["status"] == "success"
    booking_id = booking_res["booking_id"]
    assert booking_res["booking"]["status"] == "PENDING_PAYMENT"

    # 3. Simulate mock payment
    pay_res = call_mcp_tool("simulate_mock_payment", {
        "order_or_booking_id": booking_id,
        "amount": total_amount,
        "payment_method": "upi",
        "scenario": "success",
        "idempotency_key": "idemp_test_mcp_pay_1"
    })
    assert pay_res["status"] == "success"
    assert pay_res["payment"]["status"] == "SUCCESS"

    # 4. Verify booking is now CONFIRMED
    status_res = call_mcp_tool("get_booking_status", {"booking_id": booking_id})
    assert status_res["status"] == "success"
    assert status_res["record"]["status"] == "CONFIRMED"

    # 5. Order confirmation voucher
    conf_res = call_mcp_tool("get_order_confirmation", {"reference_id": booking_id})
    assert conf_res["status"] == "success"
    assert conf_res["reference_id"] == booking_id

