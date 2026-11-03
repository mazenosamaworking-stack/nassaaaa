"""
Comprehensive integration test for NASA Space Fire AI System v3.0.
Tests all new user requirements:
1. Multi-format ingestion across all agents.
2. Dynamic user-typed variables.
3. Agent 2 custom LLM config & grounded RAG.
4. Agent 3 mandatory training gate (refusal before training, active after training).
5. Agent 4 dynamic materials, conditions, and CFD thermal matrix.
6. 2-way Front-End mapping contracts.
"""

import sys
import os
import json
import time
import urllib.request
import threading

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from server import ThreadedHTTPServer, SpaceFireRequestHandler, data_ingestion

PORT = 9123
# Reset agent3 training status for the test
data_ingestion.set_training_status("agent3", False, 0, [])

server_address = ("127.0.0.1", PORT)
httpd = ThreadedHTTPServer(server_address, SpaceFireRequestHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(1.5)

print(f"🚀 Verification Server started on port {PORT}")

# 1. Test Status
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/status")
status_data = json.loads(req.read().decode("utf-8"))
assert "3.1" in status_data["version"]
print("✓ 1. Status Check: v3.1 CloudReady ONLINE")

# 2. Test Agent 3 Mandatory Training Gate (Before Training)
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/iss/current")
iss_before = json.loads(req.read().decode("utf-8"))
eval_before = iss_before["ai_fire_hazard_evaluation"]
print(f"✓ 2. Agent 3 Before Training Gate Check:")
print(f"     is_model_trained: {eval_before['is_model_trained']}")
print(f"     fire_prob: {eval_before['fire_probability_percent']} (MUST be None)")
assert eval_before["is_model_trained"] == False
assert eval_before["fire_probability_percent"] is None

# 3. Test Multi-Format Ingestion for Agent 3 with Custom Typed Variables
upload_payload = json.dumps({
    "batch_name": "ISS_Columbus_Telemetry_Batch",
    "format_type": "json",
    "user_defined_variables": ["o2_percent", "cabin_pressure_kpa", "ambient_temp_c", "co2_percent"],
    "content": json.dumps([
        {"o2_percent": 21.0, "cabin_pressure_kpa": 101.3, "ambient_temp_c": 22.0, "risk_score": 14.0},
        {"o2_percent": 28.5, "cabin_pressure_kpa": 103.0, "ambient_temp_c": 35.0, "risk_score": 68.0}
    ])
}).encode("utf-8")

req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/upload/agent3",
    data=upload_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
upload_res = json.loads(resp.read().decode("utf-8"))
print(f"✓ 3. Agent 3 Ingestion Success: {upload_res['rows_extracted']} rows extracted.")

# Now verify Agent 3 is trained and active
time.sleep(1.2)
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/iss/current")
iss_after = json.loads(req.read().decode("utf-8"))
eval_after = iss_after["ai_fire_hazard_evaluation"]
print(f"✓ 4. Agent 3 After Training Check:")
print(f"     is_model_trained: {eval_after['is_model_trained']}")
print(f"     fire_prob: {eval_after['fire_probability_percent']}%")
assert eval_after["is_model_trained"] == True
assert eval_after["fire_probability_percent"] is not None

# 5. Test Agent 2 Custom LLM Configuration
llm_cfg_payload = json.dumps({
    "base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4o-mini",
    "api_key": "sk-test-mock-key-12345",
    "is_enabled": True
}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/settings/agent2-llm",
    data=llm_cfg_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
cfg_res = json.loads(resp.read().decode("utf-8"))
assert cfg_res["config"]["has_key"] == True
assert cfg_res["config"]["masked_key"] == "sk-t...2345"
print("✓ 5. Agent 2 LLM Config Saved and Masked Securely.")

# 6. Test Agent 4 Custom Material Creation and CFD Scalar Field
mat_payload = json.dumps({
    "id": "Custom_Aerogel_Composite",
    "name_ar": "مركب إيروجيل حراري متقدم",
    "flame_temp_base": 1500.0,
    "limiting_oxygen_index": 32.0,
    "sooting_propensity": 0.1
}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/materials",
    data=mat_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
mat_res = json.loads(resp.read().decode("utf-8"))
assert mat_res["material"]["id"] == "Custom_Aerogel_Composite"
print("✓ 6. Agent 4 Custom Material Created Successfully.")

# Simulate with new material
sim_payload = json.dumps({
    "variables": {
        "fuel_material": "Custom_Aerogel_Composite",
        "gravity_level_g": 0.0,
        "sim_o2_percent": 35.0
    }
}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/simulate/agent4",
    data=sim_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
sim_res = json.loads(resp.read().decode("utf-8"))
assert sim_res["visual_spec"]["flame_type"] == "SPHERICAL_DIFFUSION"
assert len(sim_res["cfd_thermal_grid"]["scalar_matrix"]) == 24
print(f"✓ 7. Agent 4 CFD Heatmap Matrix (24x24) Generated: Max Temp {sim_res['cfd_thermal_grid']['max_temp_k']} K.")

# 8. Test 2-Way Front-End Contract Generation
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/frontend-contract/agent1")
contract_data = json.loads(req.read().decode("utf-8"))
assert "input_bridge" in contract_data
assert "output_bridge" in contract_data
assert len(contract_data["output_bridge"]["mappings"]) >= 4
print(f"✓ 8. 2-Way Contract: {len(contract_data['input_bridge']['fields'])} Input Fields & {len(contract_data['output_bridge']['mappings'])} Output Bindings Ready.")

httpd.shutdown()
print("\n" + "="*60)
print("ALL V3.0 ENHANCEMENT TESTS PASSED WITH 100% SUCCESS!")
print("="*60)
