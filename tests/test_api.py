import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from starlette.testclient import TestClient

def test_full_pipeline():
    client = TestClient(app)

    # 1. Health check
    r_h = client.get('/api/v1/health')
    assert r_h.status_code == 200, f'Health failed: {r_h.text}'
    print('[PASS] Health check:', r_h.json()['status'])

    # 2. Stops search
    r_s = client.get('/api/v1/stops/search?q=anand')
    assert r_s.status_code == 200, f'Stops search failed: {r_s.text}'
    print('[PASS] Stops search found:', len(r_s.json()['results']), 'stops')

    # 3. Popular presets
    r_p = client.get('/api/v1/stops/popular')
    assert r_p.status_code == 200
    print('[PASS] Popular presets count:', len(r_p.json()['presets']))

    # 4. Journey Plan
    r_j = client.post('/api/v1/journey/plan', json={
        'from_stop': 'Anand Vihar ISBT',
        'to_stop': 'Connaught Place',
        'departure_time': '18:00',
        'preference': 'fastest'
    })
    assert r_j.status_code == 200, f'Journey plan failed: {r_j.text}'
    opts = r_j.json()['options']
    print('[PASS] Journey plan options generated:', len(opts))
    for i, o in enumerate(opts):
        print(f"   Option {i+1}: {o['route_name']} ({o['duration_minutes']}m) -> {o['overall_crowding_level']} (Comfort: {o['comfort_score']})")

    # 5. Corridors Diagnostics
    r_c = client.get('/api/v1/crowding/corridors')
    assert r_c.status_code == 200
    print('[PASS] Overcrowded corridors analyzed:', len(r_c.json()['overcrowded_corridors']))
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_full_pipeline()
