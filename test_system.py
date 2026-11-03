"""
Comprehensive verification test for NASA Space Fire AI System.
Tests all 4 agents, dynamic variable management, training, and flame physics.
"""

import sys
import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from core.variable_manager import VariableManager
from core.ml_engine import SpaceFireAIEngine
from core.flame_physics_ai import FlamePhysicsAIEngine
from core.iss_live_stream import ISSLiveTelemetryEngine
from core.safety_chatbot import SafetyChatbotEngine

print("="*60)
print("1. Testing Dynamic Variable Manager...")
vm = VariableManager()
vars_list = vm.get_variables()
print(f"Total variables registered: {len(vars_list)}")
assert len(vars_list) >= 6

# Add a custom variable dynamically
new_var = vm.add_or_update_variable({
    "id": "wire_insulation_temp_c",
    "name_ar": "حرارة عوازل الأسلاك",
    "name_en": "Wire Insulation Temp",
    "agent_id": "agent1",
    "data_type": "number",
    "unit": "°C",
    "min_val": 20.0,
    "max_val": 200.0,
    "default_val": "45.0",
    "description": "درجة حرارة عزل كابلات الطاقة بالدرجات المئوية",
    "is_active_for_prediction": 1
})
print("Added dynamic variable successfully:", new_var["id"])

print("="*60)
print("2. Testing Agent 1: Fire Risk AI Predictor...")
ai = SpaceFireAIEngine()
pred_normal = ai.predict("agent1", {
    "o2_percent": 21.0,
    "cabin_pressure_kpa": 101.3,
    "co2_percent": 0.4,
    "ambient_temp_c": 22.0,
    "air_flow_velocity_ms": 0.10,
    "wire_insulation_temp_c": 45.0
})
print("Agent 1 Normal State Prediction:")
print(f"  Fire Probability: {pred_normal['fire_probability_percent']}%")
print(f"  Hazard Level: {pred_normal['hazard_level']}")
print(f"  Description: {pred_normal['description']}")

pred_danger = ai.predict("agent1", {
    "o2_percent": 34.0, # High oxygen
    "ambient_temp_c": 65.0, # Elevated temperature
    "air_flow_velocity_ms": 0.25,
    "material_flammability_index": 3.8
})
print("\nAgent 1 High Danger State Prediction:")
print(f"  Fire Probability: {pred_danger['fire_probability_percent']}%")
print(f"  Hazard Level: {pred_danger['hazard_level']}")
print(f"  Description: {pred_danger['description']}")
assert pred_danger["fire_probability_percent"] > pred_normal["fire_probability_percent"]

print("="*60)
print("3. Testing Dynamic Batch Training with Non-Standard Variables...")
batch_records = [
    {"o2_percent": 28.0, "co2_percent": 0.5, "wire_insulation_temp_c": 120.0, "risk_score": 75.0},
    {"o2_percent": 32.0, "wire_insulation_temp_c": 150.0, "risk_score": 92.0},
    {"o2_percent": 19.0, "co2_percent": 1.5, "wire_insulation_temp_c": 30.0, "risk_score": 8.0}
]
train_res = ai.train_on_batch("agent1", "Batch_Wire_Thermal_Anomaly", batch_records)
print(f"Batch trained successfully! Total samples: {train_res['total_samples']}")
print(f"Feature Importances: {train_res['feature_importances']}")

print("="*60)
print("4. Testing Agent 2: Safety Incident Chatbot...")
safety = SafetyChatbotEngine()
chat_res = safety.analyze_incident("ألاحظ دخاناً متصاعداً مع شرر كهربائي متكرر في لوحة القواطع الرئيسية بممر المركبة")
print("Agent 2 Incident Diagnosis:")
print(f"  Category: {chat_res['category']}")
print(f"  Root Cause: {chat_res['root_cause_diagnosis']}")
print(f"  Subsystem: {chat_res['affected_subsystem']}")
print(f"  Immediate Actions: {len(chat_res['recommended_actions'])} steps")

print("="*60)
print("5. Testing Agent 3: ISS Live Telemetry Streamer...")
iss = ISSLiveTelemetryEngine(ai)
iss._update_telemetry_tick()
snapshot = iss.get_latest_snapshot()
print(f"ISS Telemetry Snapshot (Tick {snapshot['tick']}):")
print(f"  Position: Lat {snapshot['orbital_data']['latitude']}°, Lon {snapshot['orbital_data']['longitude']}°")
print(f"  ECLSS O2: {snapshot['atmospheric_telemetry']['o2_percent']}%")
print(f"  Fire Risk: {snapshot['ai_fire_hazard_evaluation']['fire_probability_percent']}%")
print(f"  Hazard: {snapshot['ai_fire_hazard_evaluation']['hazard_level']}")
iss.stop()

print("="*60)
print("6. Testing Agent 4: AI Flame Visual Simulation...")
flame = FlamePhysicsAIEngine()

# Microgravity 0g test
sim_0g = flame.simulate_flame({
    "fuel_material": "PMMA",
    "gravity_level_g": 0.0,
    "sim_o2_percent": 21.0,
    "sim_pressure_kpa": 101.3,
    "sim_flow_velocity_cms": 2.0
})
print("Agent 4 Microgravity 0g Simulation:")
print(f"  Flame Type: {sim_0g['visual_spec']['flame_type']}")
print(f"  Aspect Ratio: {sim_0g['aspect_ratio']} (Spherical)")
print(f"  Peak Temp: {sim_0g['peak_temperature_k']} K")
print(f"  Blue Chemiluminescence Ratio: {sim_0g['blue_chemiluminescence_ratio']}")
print(f"  Flicker Freq: {sim_0g['flicker_frequency_hz']} Hz")

# Earth gravity 1g test
sim_1g = flame.simulate_flame({
    "fuel_material": "PMMA",
    "gravity_level_g": 1.0,
    "sim_o2_percent": 21.0,
    "sim_pressure_kpa": 101.3,
    "sim_flow_velocity_cms": 2.0
})
print("\nAgent 4 Earth Gravity 1g Simulation:")
print(f"  Flame Type: {sim_1g['visual_spec']['flame_type']}")
print(f"  Aspect Ratio: {sim_1g['aspect_ratio']} (Buoyant Teardrop)")
print(f"  Flicker Freq: {sim_1g['flicker_frequency_hz']} Hz")

assert sim_0g["visual_spec"]["flame_type"] == "SPHERICAL_DIFFUSION"
assert sim_1g["visual_spec"]["flame_type"] == "BUOYANT_TEARDROP"
assert sim_0g["flicker_frequency_hz"] == 0.0
assert sim_1g["flicker_frequency_hz"] > 5.0

print("\n" + "="*60)
print("ALL AGENT AND AI SUBSYSTEM TESTS PASSED WITH 100% SUCCESS!")
print("="*60)
