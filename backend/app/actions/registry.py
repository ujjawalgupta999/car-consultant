"""
Universal Website Action Registry for Aura AI Consultant.
Defines every supported website operation, its input schema, execution handler,
navigation route, and frontend action mapping.
"""

from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger("car_consultant.actions")

class ActionParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False
    default: Optional[Any] = None

class ActionDefinition(BaseModel):
    name: str
    description: str
    intent: str
    category: str # "NAVIGATION", "VEHICLES", "ACCOUNT", "TRANSACTIONS", "WORKFLOW"
    parameters: List[ActionParameter] = Field(default_factory=list)
    requires_auth: bool = False
    requires_confirmation: bool = False
    navigation_path: Optional[str] = None
    ui_action_type: str = "NAVIGATE"

class WebsiteActionRegistry:
    """
    Centralized registry of all executable website actions that the AI agent can invoke.
    """
    def __init__(self):
        self._actions: Dict[str, ActionDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._register_default_actions()

    def register_action(
        self,
        action: ActionDefinition,
        handler: Optional[Callable] = None
    ):
        self._actions[action.name] = action
        if handler:
            self._handlers[action.name] = handler

    def get_action(self, name: str) -> Optional[ActionDefinition]:
        return self._actions.get(name)

    def get_all_actions(self) -> List[ActionDefinition]:
        return list(self._actions.values())

    def get_actions_by_intent(self, intent: str) -> List[ActionDefinition]:
        return [a for a in self._actions.values() if a.intent == intent]

    def _register_default_actions(self):
        # -------------------------------------------------------------
        # 1. ACCOUNT ACTIONS
        # -------------------------------------------------------------
        self.register_action(ActionDefinition(
            name="view_my_vehicles",
            description="Retrieve and display all vehicles purchased and owned by the authenticated user",
            intent="VIEW_MY_VEHICLES",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/purchases",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_my_purchases",
            description="Retrieve and display the authenticated user's confirmed vehicle purchases and order history",
            intent="VIEW_PURCHASES",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/purchases",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_my_rentals",
            description="Retrieve and display the authenticated user's vehicle orders (redirects to purchases)",
            intent="VIEW_RENTALS",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/purchases",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_my_listings",
            description="Retrieve and display vehicles currently listed for sale by the user on the marketplace",
            intent="VIEW_SELLING_LISTINGS",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/listings",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_payment_history",
            description="Retrieve and display the authenticated user's payment records, transaction receipts, and billing history",
            intent="VIEW_PAYMENT_HISTORY",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/payments",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_saved_vehicles",
            description="Retrieve and display vehicles bookmarked/saved by the user",
            intent="VIEW_SAVED_VEHICLES",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/saved",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_user_profile",
            description="View account profile, verified KYC credentials, and personal details",
            intent="UPDATE_PROFILE",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard/profile",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="view_dashboard_overview",
            description="View the primary user dashboard summary overview with analytics",
            intent="VIEW_DASHBOARD",
            category="ACCOUNT",
            requires_auth=True,
            navigation_path="/dashboard",
            ui_action_type="NAVIGATE"
        ))

        # -------------------------------------------------------------
        # 2. VEHICLE SEARCH & CATALOGUE ACTIONS
        # -------------------------------------------------------------
        self.register_action(ActionDefinition(
            name="search_vehicles_buy",
            description="Search, filter, and display vehicles available for purchase based on category, budget, transmission, fuel type, and brand",
            intent="SEARCH_VEHICLES",
            category="VEHICLES",
            parameters=[
                ActionParameter(name="category", type="string", description="Vehicle style: SUV, Sedan, EV, Hatchback, Convertible"),
                ActionParameter(name="max_price", type="number", description="Maximum purchase budget in INR"),
                ActionParameter(name="min_price", type="number", description="Minimum purchase budget in INR"),
                ActionParameter(name="brand", type="string", description="Preferred manufacturer brand"),
                ActionParameter(name="transmission", type="string", description="Automatic or Manual"),
                ActionParameter(name="fuel_type", type="string", description="Petrol, Diesel, Electric, Hybrid, CNG"),
                ActionParameter(name="location", type="string", description="City location")
            ],
            navigation_path="/buy",
            ui_action_type="FILTER_VEHICLES"
        ))

        self.register_action(ActionDefinition(
            name="search_vehicles_rent",
            description="Search, filter, and display rental fleet vehicles based on category, city, daily budget, and duration",
            intent="RENT_VEHICLE",
            category="VEHICLES",
            parameters=[
                ActionParameter(name="category", type="string", description="Vehicle style: SUV, Sedan, EV, Hatchback"),
                ActionParameter(name="location", type="string", description="City: Delhi, Mumbai, Bangalore, etc."),
                ActionParameter(name="max_daily_price", type="number", description="Maximum daily rental rate in INR"),
                ActionParameter(name="pickup_date", type="string", description="Pickup start date"),
                ActionParameter(name="duration_days", type="integer", description="Rental duration in days")
            ],
            navigation_path="/rent",
            ui_action_type="FILTER_VEHICLES"
        ))

        self.register_action(ActionDefinition(
            name="compare_vehicles",
            description="Set up side-by-side technical comparison between two or more vehicles and open comparison page",
            intent="COMPARE_VEHICLES",
            category="VEHICLES",
            parameters=[
                ActionParameter(name="vehicle_ids", type="list", description="List of vehicle IDs to compare", required=True)
            ],
            navigation_path="/compare",
            ui_action_type="ADD_TO_COMPARISON"
        ))

        self.register_action(ActionDefinition(
            name="open_vehicle_details",
            description="Navigate directly to vehicle detailed specification and gallery page",
            intent="VIEW_VEHICLE_DETAILS",
            category="VEHICLES",
            parameters=[
                ActionParameter(name="vehicle_id", type="string", description="ID of vehicle", required=True)
            ],
            navigation_path="/vehicles/{vehicle_id}",
            ui_action_type="SELECT_VEHICLE"
        ))

        # -------------------------------------------------------------
        # 3. SELLING WORKFLOW ACTIONS
        # -------------------------------------------------------------
        self.register_action(ActionDefinition(
            name="start_sell_workflow",
            description="Initiate selling workflow, optionally prefilled with one of the user's owned vehicles, and navigate to sell car portal",
            intent="SELL_VEHICLE",
            category="WORKFLOW",
            parameters=[
                ActionParameter(name="brand", type="string", description="Vehicle brand"),
                ActionParameter(name="model", type="string", description="Vehicle model"),
                ActionParameter(name="year", type="integer", description="Manufacturing year"),
                ActionParameter(name="expected_price", type="number", description="Expected selling price in INR"),
                ActionParameter(name="kms_driven", type="integer", description="Odometer reading in km"),
                ActionParameter(name="owned_vehicle_id", type="string", description="ID of owned vehicle to sell")
            ],
            navigation_path="/sell-car",
            ui_action_type="UPDATE_FORM"
        ))

        # -------------------------------------------------------------
        # 4. BOOKING & CHECKOUT ACTIONS
        # -------------------------------------------------------------
        self.register_action(ActionDefinition(
            name="start_checkout",
            description="Initiate checkout session for vehicle purchase or rental and navigate to secure checkout page",
            intent="CHECKOUT",
            category="TRANSACTIONS",
            parameters=[
                ActionParameter(name="order_id", type="string", description="Order or Booking ID", required=True)
            ],
            navigation_path="/checkout/{order_id}",
            ui_action_type="NAVIGATE"
        ))

        self.register_action(ActionDefinition(
            name="cancel_booking",
            description="Cancel an existing rental reservation or purchase order",
            intent="CANCEL_BOOKING",
            category="TRANSACTIONS",
            requires_auth=True,
            requires_confirmation=True,
            parameters=[
                ActionParameter(name="order_or_booking_id", type="string", description="Order or Booking ID", required=True)
            ],
            navigation_path="/dashboard/rentals",
            ui_action_type="SHOW_NOTIFICATION"
        ))

        # -------------------------------------------------------------
        # 5. GENERAL NAVIGATION
        # -------------------------------------------------------------
        self.register_action(ActionDefinition(
            name="navigate_to_page",
            description="Navigate directly to any route on the website",
            intent="NAVIGATE",
            category="NAVIGATION",
            parameters=[
                ActionParameter(name="path", type="string", description="Target route path", required=True)
            ],
            navigation_path="{path}",
            ui_action_type="NAVIGATE"
        ))

action_registry = WebsiteActionRegistry()

