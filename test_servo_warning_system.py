"""
SafeSight AI - Root Launcher for SG90 Dynamic Warning System
Redirects execution to BLINDSPOT PROJ/test_servo_warning_system.py
"""
import sys
import os

target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BLINDSPOT PROJ")
target_script = os.path.join(target_dir, "test_servo_warning_system.py")

if not os.path.exists(target_script):
    print(f"❌ Error: Could not find target script at {target_script}")
    sys.exit(1)

# Ensure Python searches BLINDSPOT PROJ and SafeSightAi for imports
if target_dir not in sys.path:
    sys.path.insert(0, target_dir)

safesight_dir = os.path.join(target_dir, "SafeSightAi")
if os.path.exists(safesight_dir) and safesight_dir not in sys.path:
    sys.path.insert(0, safesight_dir)

# Run the target script
with open(target_script, "r", encoding="utf-8") as f:
    code = compile(f.read(), target_script, "exec")
    exec(code, {"__name__": "__main__", "__file__": target_script})
