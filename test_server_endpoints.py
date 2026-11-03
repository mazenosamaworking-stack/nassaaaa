"""
Server endpoint integration test. Starts server in-process, tests HTTP requests, shuts down.
"""

import sys
import os
import json
import time
import urllib.request
import threading

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from server import ThreadedHTTPServer, SpaceFireRequestHandler

PORT = 8999
server_address = ("127.0.0.1", PORT)
httpd = ThreadedHTTPServer(server_address, SpaceFireRequestHandler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
time.sleep(0.5)

print(f"Server started on port {PORT}")

# 1. Test GET /api/status
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/status")
status_data = json.loads(req.read().decode("utf-8"))
print("Status response:", status_data["system"], status_data["status"])
assert status_data["status"] == "ONLINE"

# 2. Test GET /api/variables
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/variables?agent_id=agent1")
vars_data = json.loads(req.read().decode("utf-8"))
print(f"Agent 1 variables count: {len(vars_data['variables'])}")

# 3. Test POST /api/predict/agent1
post_data = json.dumps({
    "variables": {
        "o2_percent": 22.5,
        "cabin_pressure_kpa": 101.3,
        "ambient_temp_c": 24.0
    }
}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/predict/agent1",
    data=post_data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
pred_resp = json.loads(resp.read().decode("utf-8"))
print("Agent 1 HTTP Prediction:", pred_resp["fire_probability_percent"], "% |", pred_resp["hazard_level_en"])

# 4. Test POST /api/chat/agent2
chat_data = json.dumps({"message": "رائحة شياط ودخان من مروحة التهوية"}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/chat/agent2",
    data=chat_data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
chat_resp = json.loads(resp.read().decode("utf-8"))
print("Agent 2 HTTP Chat category:", chat_resp["category"])

# 5. Test GET /api/iss/current
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/iss/current")
iss_resp = json.loads(req.read().decode("utf-8"))
print("Agent 3 ISS snapshot tick:", iss_resp.get("tick"))

# 6. Test POST /api/simulate/agent4
sim_data = json.dumps({
    "variables": {
        "fuel_material": "Heptane",
        "gravity_level_g": 0.0,
        "sim_o2_percent": 21.0
    }
}).encode("utf-8")
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/api/simulate/agent4",
    data=sim_data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
sim_resp = json.loads(resp.read().decode("utf-8"))
print("Agent 4 Simulation:", sim_resp["visual_spec"]["flame_type"], "| Peak Temp:", sim_resp["peak_temperature_k"])

# 7. Test Static File GET /
req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/")
html = req.read().decode("utf-8")
print("Static index.html served length:", len(html), "bytes")
assert "<!DOCTYPE html>" in html

httpd.shutdown()
print("All server endpoint tests passed cleanly!")
