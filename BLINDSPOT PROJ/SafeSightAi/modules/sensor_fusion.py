"""
SafeSight AI - Two-Sensor Fusion Engine
Combines Camera-based Human Detection (YOLOv8) with HC-SR04 Ultrasonic Physical Proximity.

Safety Principle:
  HUMAN_DETECTED == true AND DISTANCE <= DANGER_THRESHOLD => HUMAN_DANGER == true
  Otherwise: HUMAN_DANGER == false

  HC-SR04 detecting an obstacle (wall, rock, tool, vehicle) alone NEVER activates the buzzer.
  The buzzer only activates when the camera confirms a human is in the danger zone.
"""

import logging

logger = logging.getLogger(__name__)

class SensorFusionEngine:
    def __init__(self, warning_threshold_cm=50.0, danger_threshold_cm=20.0, critical_threshold_cm=10.0):
        self.warning_threshold_cm = warning_threshold_cm
        self.danger_threshold_cm = danger_threshold_cm
        self.critical_threshold_cm = critical_threshold_cm

    def evaluate(self, human_detected, distance_cm, worker_id=1):
        """
        Evaluate threat level by fusing camera human detection with ultrasonic proximity.

        Args:
            human_detected (bool): True if camera/AI identified at least one person/worker.
            distance_cm (float): Physical distance in cm from HC-SR04 (-1 if invalid or no echo).
            worker_id (int): Worker/person identifier if tracked.

        Returns:
            dict: {
                "zone": "SAFE" | "WARNING" | "DANGER" | "CRITICAL",
                "human_detected": bool,
                "distance_cm": float,
                "alarm_active": bool,
                "reason": str,
                "worker_id": int
            }
        """
        # RULE 1: If NO human is detected by the camera, the alarm is strictly SAFE!
        # Even if distance is 2 cm (wall, rock, machine), NO human alarm sounds.
        if not human_detected:
            return {
                "zone": "SAFE",
                "human_detected": False,
                "distance_cm": distance_cm,
                "alarm_active": False,
                "reason": "Safe: No human detected by camera (non-human obstacles ignored)",
                "worker_id": worker_id
            }

        # RULE 2: Human detected, but HC-SR04 sees no close obstacle or is out of range
        if distance_cm <= 0 or distance_cm > self.warning_threshold_cm:
            return {
                "zone": "SAFE",
                "human_detected": True,
                "distance_cm": distance_cm,
                "alarm_active": False,
                "reason": f"Safe: Human present, but outside warning range ({distance_cm:.1f} cm > {self.warning_threshold_cm:.1f} cm)",
                "worker_id": worker_id
            }

        # RULE 3: Human detected and approaching (danger_threshold < distance <= warning_threshold)
        if distance_cm > self.danger_threshold_cm:
            return {
                "zone": "WARNING",
                "human_detected": True,
                "distance_cm": distance_cm,
                "alarm_active": True,
                "reason": f"Warning: Human approaching danger zone ({distance_cm:.1f} cm)",
                "worker_id": worker_id
            }

        # RULE 4: Human detected inside danger zone (critical_threshold < distance <= danger_threshold)
        if distance_cm > self.critical_threshold_cm:
            return {
                "zone": "DANGER",
                "human_detected": True,
                "distance_cm": distance_cm,
                "alarm_active": True,
                "reason": f"DANGER: Human inside danger zone ({distance_cm:.1f} cm)!",
                "worker_id": worker_id
            }

        # RULE 5: Human detected at critical proximity (distance <= critical_threshold)
        return {
            "zone": "CRITICAL",
            "human_detected": True,
            "distance_cm": distance_cm,
            "alarm_active": True,
            "reason": f"CRITICAL: Human at immediate risk ({distance_cm:.1f} cm)!",
            "worker_id": worker_id
        }
