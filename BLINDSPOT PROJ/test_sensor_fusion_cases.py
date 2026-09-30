"""
SafeSight AI - Sensor Fusion Verification Test
Directly validates the 6 core safety test cases from the project specification:
  - Non-human objects close to sensor MUST NOT trigger alarms.
  - Humans outside danger distance MUST NOT trigger alarms.
  - Humans inside danger distance MUST trigger the appropriate alarm.
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

current_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = current_dir if os.path.exists(os.path.join(current_dir, 'modules')) else os.path.join(current_dir, 'SafeSightAi')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from modules.sensor_fusion import SensorFusionEngine

def run_tests():
    engine = SensorFusionEngine(
        warning_threshold_cm=50.0,
        danger_threshold_cm=20.0,
        critical_threshold_cm=10.0
    )

    test_cases = [
        {
            "id": "CASE 1",
            "name": "Human far away",
            "human_detected": True,
            "distance_cm": 100.0,
            "expected_zone": "SAFE",
            "expected_alarm": False
        },
        {
            "id": "CASE 2",
            "name": "Human inside danger zone (15 cm)",
            "human_detected": True,
            "distance_cm": 15.0,
            "expected_zone": "DANGER",
            "expected_alarm": True
        },
        {
            "id": "CASE 3",
            "name": "Wall inside danger zone (10 cm) - NOT HUMAN",
            "human_detected": False,
            "distance_cm": 10.0,
            "expected_zone": "SAFE",
            "expected_alarm": False
        },
        {
            "id": "CASE 4",
            "name": "Rock inside danger zone (12 cm) - NOT HUMAN",
            "human_detected": False,
            "distance_cm": 12.0,
            "expected_zone": "SAFE",
            "expected_alarm": False
        },
        {
            "id": "CASE 5",
            "name": "Human detected but HC-SR04 sees no close obstacle",
            "human_detected": True,
            "distance_cm": -1.0,
            "expected_zone": "SAFE",
            "expected_alarm": False
        },
        {
            "id": "CASE 6",
            "name": "Human at critical proximity (6 cm)",
            "human_detected": True,
            "distance_cm": 6.0,
            "expected_zone": "CRITICAL",
            "expected_alarm": True
        },
        {
            "id": "CASE 7",
            "name": "Human approaching (35 cm warning zone)",
            "human_detected": True,
            "distance_cm": 35.0,
            "expected_zone": "WARNING",
            "expected_alarm": True
        }
    ]

    print("=" * 70)
    print(" SafeSight AI - Sensor Fusion Specification Verification")
    print("=" * 70)
    print()

    all_passed = True
    for case in test_cases:
        res = engine.evaluate(case["human_detected"], case["distance_cm"])
        zone_match = (res["zone"] == case["expected_zone"])
        alarm_match = (res["alarm_active"] == case["expected_alarm"])
        passed = zone_match and alarm_match

        if not passed:
            all_passed = False

        status_str = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{case['id']}] {case['name']}")
        print(f"   Inputs:    Human={case['human_detected']}, Distance={case['distance_cm']} cm")
        print(f"   Outcome:   Zone={res['zone']}, AlarmActive={res['alarm_active']} -> {status_str}")
        print(f"   Reason:    {res['reason']}")
        print()

    print("=" * 70)
    if all_passed:
        print(" 🎉 ALL SENSOR FUSION SPECIFICATION TESTS PASSED (7/7)!")
    else:
        print(" ❌ Some tests failed.")
    print("=" * 70)
    return all_passed

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
