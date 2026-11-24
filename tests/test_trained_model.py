import requests

def test_predictions():
    # 1. Evening Peak (6:00 PM IST)
    r1 = requests.post('http://127.0.0.1:8000/api/v1/journey/plan', json={
        'from_stop': 'Anand Vihar ISBT',
        'to_stop': 'Connaught Place',
        'departure_time': '18:00',
        'preference': 'balanced'
    })
    print('Peak Status:', r1.status_code)
    opts1 = r1.json()['options']
    print(f'Retrieved {len(opts1)} options at 6:00 PM IST:')
    for o in opts1:
        print(f"  {o['route_name']} ({o['duration_minutes']}m) -> {o['overall_crowding_level']} ({o['overall_occupancy_ratio']*100:.0f}% load, Comfort: {o['comfort_score']})")

    # 2. Afternoon Off-Peak (1:00 PM IST)
    r2 = requests.post('http://127.0.0.1:8000/api/v1/journey/plan', json={
        'from_stop': 'Anand Vihar ISBT',
        'to_stop': 'Connaught Place',
        'departure_time': '13:00',
        'preference': 'balanced'
    })
    print(f'\nOff-peak Status:', r2.status_code)
    opts2 = r2.json()['options']
    print(f'Retrieved {len(opts2)} options at 1:00 PM IST:')
    for o in opts2:
        print(f"  {o['route_name']} ({o['duration_minutes']}m) -> {o['overall_crowding_level']} ({o['overall_occupancy_ratio']*100:.0f}% load, Comfort: {o['comfort_score']})")

if __name__ == '__main__':
    test_predictions()
