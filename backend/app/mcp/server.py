from typing import Dict, Any, List
import logging
from . import tools

logger = logging.getLogger(__name__)

MCP_TOOL_DEFINITIONS = [
    {
        "name": "search_vehicles",
        "description": "Searches and filters vehicle listings across categories, budget, dates, and locations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["rent", "buy"], "default": "rent"},
                "location": {"type": "string"},
                "category": {"type": "string"},
                "max_price": {"type": "number"},
                "transmission": {"type": "string"},
                "fuel_type": {"type": "string"},
                "seats": {"type": "integer"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            }
        }
    },
    {
        "name": "get_vehicle_details",
        "description": "Fetches detailed specifications and features for a vehicle by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"}
            },
            "required": ["vehicle_id"]
        }
    },
    {
        "name": "check_vehicle_availability",
        "description": "Validates date conflicts for renting a vehicle during the requested date range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            },
            "required": ["vehicle_id", "start_date", "end_date"]
        }
    },
    {
        "name": "compare_vehicles",
        "description": "Compares multiple vehicle listings side by side.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vehicle_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["vehicle_ids"]
        }
    },
    {
        "name": "calculate_booking_total",
        "description": "Computes authoritative rental pricing, add-ons, taxes, and final total.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vehicle_id": {"type": "string"},
                "duration_days": {"type": "integer"},
                "addon_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["vehicle_id", "duration_days"]
        }
    },
    {
        "name": "create_booking",
        "description": "Creates a verified pending vehicle rental booking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "vehicle_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"},
                "customer_phone": {"type": "string"},
                "driver_license_number": {"type": "string"},
                "pickup_date": {"type": "string"},
                "return_date": {"type": "string"},
                "duration_days": {"type": "integer"},
                "pickup_location": {"type": "string"},
                "return_location": {"type": "string"},
                "addon_ids": {"type": "array", "items": {"type": "string"}},
                "idempotency_key": {"type": "string"}
            },
            "required": [
                "session_id", "vehicle_id", "customer_name", "customer_email",
                "customer_phone", "driver_license_number", "pickup_date",
                "return_date", "duration_days", "pickup_location", "return_location"
            ]
        }
    },
    {
        "name": "create_purchase_order",
        "description": "Creates a pending purchase order reservation for a vehicle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "vehicle_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"},
                "customer_phone": {"type": "string"},
                "pan_or_id": {"type": "string"},
                "delivery_city": {"type": "string"},
                "financing_selected": {"type": "boolean"},
                "deposit_amount": {"type": "number"},
                "idempotency_key": {"type": "string"}
            },
            "required": [
                "session_id", "vehicle_id", "customer_name",
                "customer_email", "customer_phone", "pan_or_id", "delivery_city"
            ]
        }
    },
    {
        "name": "get_booking_status",
        "description": "Retrieves the status of an existing booking or purchase order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "booking_id": {"type": "string"}
            },
            "required": ["booking_id"]
        }
    },
    {
        "name": "simulate_mock_payment",
        "description": "Executes simulated mock payment with success, failure, or timeout scenario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_or_booking_id": {"type": "string"},
                "amount": {"type": "number"},
                "payment_method": {"type": "string", "enum": ["upi", "card", "netbanking"]},
                "scenario": {"type": "string", "enum": ["success", "failure", "timeout"]},
                "idempotency_key": {"type": "string"}
            },
            "required": ["order_or_booking_id", "amount"]
        }
    },
    {
        "name": "get_order_confirmation",
        "description": "Fetches verified final confirmation receipt for a booking or order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reference_id": {"type": "string"}
            },
            "required": ["reference_id"]
        }
    }
]

def list_mcp_tools() -> List[Dict[str, Any]]:
    return MCP_TOOL_DEFINITIONS

def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    tool_map = {
        "search_vehicles": tools.tool_search_vehicles,
        "get_vehicle_details": tools.tool_get_vehicle_details,
        "check_vehicle_availability": tools.tool_check_vehicle_availability,
        "compare_vehicles": tools.tool_compare_vehicles,
        "calculate_booking_total": tools.tool_calculate_booking_total,
        "create_booking": tools.tool_create_booking,
        "create_purchase_order": tools.tool_create_purchase_order,
        "get_booking_status": tools.tool_get_booking_status,
        "simulate_mock_payment": tools.tool_simulate_mock_payment,
        "get_order_confirmation": tools.tool_get_order_confirmation,
    }

    if tool_name not in tool_map:
        return {"status": "error", "message": f"Tool '{tool_name}' is not registered."}

    handler = tool_map[tool_name]
    try:
        return handler(**arguments)
    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

