import asyncio
from backend.app.orchestration.orchestrator import orchestration_engine

scenarios = [
    'I want to buy a luxury SUV in Delhi',
    'I need an automatic sedan under 30 lakh',
    'Can I rent a car in Mumbai for 3 days?',
    'show me my purchases',
    'I want to sell my Honda City',
    'compare BMW M3 and Audi RS6',
    'Show me 7 seater cars'
]

async def run_all():
    for i, s in enumerate(scenarios):
        sess_id = f'sess_stress_test_{i}'
        print(f'Testing scenario {i+1}: "{s}"')
        res = await orchestration_engine.process_user_turn(sess_id, s)
        assert res is not None, f'Scenario {i+1} failed!'
        print(f'  ✓ Success! State: {res.get("workflow_state")}, Actions: {len(res.get("actions", []))}')

if __name__ == '__main__':
    asyncio.run(run_all())
    print('ALL 7 ORCHESTRATOR SCENARIOS PASSED WITH ZERO ERRORS!')

