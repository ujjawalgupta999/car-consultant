import pytest
from backend.app.models.session import WorkflowState
from backend.app.orchestration.state_machine import StateMachine, InvalidStateTransitionError

def test_legal_state_transitions():
    assert StateMachine.validate_transition(WorkflowState.NEW, WorkflowState.INTERVIEWING) is True
    assert StateMachine.validate_transition(WorkflowState.INTERVIEWING, WorkflowState.READY_TO_SEARCH) is True
    assert StateMachine.validate_transition(WorkflowState.READY_TO_SEARCH, WorkflowState.SEARCHING) is True
    assert StateMachine.validate_transition(WorkflowState.SEARCHING, WorkflowState.RANKING) is True
    assert StateMachine.validate_transition(WorkflowState.RANKING, WorkflowState.RECOMMENDATIONS_READY) is True
    assert StateMachine.validate_transition(WorkflowState.RECOMMENDATIONS_READY, WorkflowState.VEHICLE_SELECTED) is True
    assert StateMachine.validate_transition(WorkflowState.VEHICLE_SELECTED, WorkflowState.BOOKING_IN_PROGRESS) is True
    assert StateMachine.validate_transition(WorkflowState.BOOKING_IN_PROGRESS, WorkflowState.CHECKOUT_READY) is True
    assert StateMachine.validate_transition(WorkflowState.CHECKOUT_READY, WorkflowState.PAYMENT_PROCESSING) is True
    assert StateMachine.validate_transition(WorkflowState.PAYMENT_PROCESSING, WorkflowState.CONFIRMED) is True

def test_illegal_state_transitions_blocked():
    # Direct jump from NEW to CHECKOUT_READY
    with pytest.raises(InvalidStateTransitionError):
        StateMachine.validate_transition(WorkflowState.NEW, WorkflowState.CHECKOUT_READY)

    # Direct jump from INTERVIEWING to CONFIRMED
    with pytest.raises(InvalidStateTransitionError):
        StateMachine.validate_transition(WorkflowState.INTERVIEWING, WorkflowState.CONFIRMED)

    # Attempt to confirm from SEARCHING
    with pytest.raises(InvalidStateTransitionError):
        StateMachine.validate_transition(WorkflowState.SEARCHING, WorkflowState.CONFIRMED)

def test_payment_failure_and_retry_transitions():
    # PAYMENT_PROCESSING -> PAYMENT_FAILED is allowed
    assert StateMachine.validate_transition(WorkflowState.PAYMENT_PROCESSING, WorkflowState.PAYMENT_FAILED) is True
    # PAYMENT_FAILED -> CHECKOUT_READY is allowed (for safe retry)
    assert StateMachine.validate_transition(WorkflowState.PAYMENT_FAILED, WorkflowState.CHECKOUT_READY) is True

