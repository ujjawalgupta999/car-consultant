from typing import Set, Dict
from ..models.session import WorkflowState

class InvalidStateTransitionError(Exception):
    def __init__(self, current_state: WorkflowState, target_state: WorkflowState, reason: str = ""):
        super().__init__(f"Invalid transition from {current_state.value} to {target_state.value}. {reason}".strip())
        self.current_state = current_state
        self.target_state = target_state

# Directed Graph of Valid Transitions
VALID_TRANSITIONS: Dict[WorkflowState, Set[WorkflowState]] = {
    WorkflowState.NEW: {
        WorkflowState.INTERVIEWING,
        WorkflowState.READY_TO_SEARCH,
        WorkflowState.SEARCHING
    },
    WorkflowState.INTERVIEWING: {
        WorkflowState.INTERVIEWING,
        WorkflowState.READY_TO_SEARCH,
        WorkflowState.SEARCHING,
        WorkflowState.CANCELLED
    },
    WorkflowState.READY_TO_SEARCH: {
        WorkflowState.SEARCHING,
        WorkflowState.INTERVIEWING,
        WorkflowState.CANCELLED
    },
    WorkflowState.SEARCHING: {
        WorkflowState.RANKING,
        WorkflowState.RECOMMENDATIONS_READY,
        WorkflowState.INTERVIEWING,
        WorkflowState.CANCELLED
    },
    WorkflowState.RANKING: {
        WorkflowState.RECOMMENDATIONS_READY,
        WorkflowState.SEARCHING,
        WorkflowState.INTERVIEWING,
        WorkflowState.CANCELLED
    },
    WorkflowState.RECOMMENDATIONS_READY: {
        WorkflowState.SEARCHING,
        WorkflowState.READY_TO_SEARCH,
        WorkflowState.INTERVIEWING,
        WorkflowState.RECOMMENDATIONS_READY,
        WorkflowState.VEHICLE_SELECTED,
        WorkflowState.CANCELLED
    },
    WorkflowState.VEHICLE_SELECTED: {
        WorkflowState.BOOKING_IN_PROGRESS,
        WorkflowState.CHECKOUT_READY,
        WorkflowState.RECOMMENDATIONS_READY,
        WorkflowState.SEARCHING,
        WorkflowState.INTERVIEWING,
        WorkflowState.CANCELLED
    },
    WorkflowState.BOOKING_IN_PROGRESS: {
        WorkflowState.CHECKOUT_READY,
        WorkflowState.VEHICLE_SELECTED,
        WorkflowState.RECOMMENDATIONS_READY,
        WorkflowState.CANCELLED
    },
    WorkflowState.CHECKOUT_READY: {
        WorkflowState.PAYMENT_PROCESSING,
        WorkflowState.BOOKING_IN_PROGRESS,
        WorkflowState.VEHICLE_SELECTED,
        WorkflowState.CANCELLED
    },
    WorkflowState.PAYMENT_PROCESSING: {
        WorkflowState.CONFIRMED,
        WorkflowState.PAYMENT_FAILED,
        WorkflowState.CANCELLED
    },
    WorkflowState.PAYMENT_FAILED: {
        WorkflowState.CHECKOUT_READY,
        WorkflowState.PAYMENT_PROCESSING,
        WorkflowState.CANCELLED
    },
    WorkflowState.CONFIRMED: {
        WorkflowState.NEW,
        WorkflowState.READY_TO_SEARCH,
        WorkflowState.SEARCHING,
        WorkflowState.INTERVIEWING
    },
    WorkflowState.CANCELLED: {
        WorkflowState.NEW,
        WorkflowState.INTERVIEWING,
        WorkflowState.SEARCHING
    }
}

class StateMachine:
    @staticmethod
    def validate_transition(current: WorkflowState, target: WorkflowState) -> bool:
        if current == target:
            return True
        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidStateTransitionError(current, target)
        return True

