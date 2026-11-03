"""
NASA Space Fire AI System - High-Performance Multi-Agent Backend Server.
Supports:
- Multi-format data ingestion for all 4 agents (CSV, Excel, JSON, PDF, Array, Image, Video, Text).
- Agent 2 Custom LLM API Hook & Data-Grounded RAG.
- Agent 3 Live NASA ISS API integration with Mandatory Training Gate.
- Agent 4 Dynamic Materials, Conditions, and CFD Scalar Field Generation with Visual Mirroring.
- 2-Way Front-End Input & Output Mapping Contracts.
"""

import os
import sys
import json
import time
import urllib.parse
from typing import Any, Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from core.variable_manager import VariableManager
from core.ml_engine import SpaceFireAIEngine
from core.flame_physics_ai import FlamePhysicsAIEngine
from core.iss_live_stream import ISSLiveTelemetryEngine
from core.safety_chatbot import SafetyChatbotEngine
from core.data_ingestion import UniversalDataIngestionEngine
from core.llm_bridge import Agent2LLMBridge

# Initialize System Engines
data_ingestion = UniversalDataIngestionEngine()
var_mgr = VariableManager()
ai_engine = SpaceFireAIEngine()
flame_engine = FlamePhysicsAIEngine()
iss_streamer = ISSLiveTelemetryEngine(ai_engine, data_engine=data_ingestion)
safety_bot = SafetyChatbotEngine()
llm_bridge = Agent2LLMBridge(data_engine=data_ingestion)

STATIC_DIR = os.path.join(CURRENT_DIR, "static")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class SpaceFireRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        if "stream" not in self.path:
            super().log_message(format, *args)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE, PUT")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json_response(self, data: Any, status_code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Determine dynamic base URL from request host & headers (production cloud / github deployment ready)
        host_header = self.headers.get("Host", "localhost:8500")
        fwd_proto = self.headers.get("X-Forwarded-Proto", "https" if ("render.com" in host_header or "railway.app" in host_header) else "http")
        public_base_url = os.environ.get("PUBLIC_API_URL", f"{fwd_proto}://{host_header}")

        # 1. System Health
        if path == "/api/status":
            self._send_json_response({
                "status": "ONLINE",
                "system": "NASA Spacecraft Multi-Agent Fire AI",
                "version": "3.1.0-CloudReady",
                "environment": os.environ.get("DEPLOY_ENV", "production"),
                "base_url": public_base_url,
                "agents": {
                    "agent1": "NASA Fire Occurrence & Hazard Predictor",
                    "agent2": "Space Fire Incident Root-Cause & Safety Chatbot (LLM-RAG)",
                    "agent3": "Real-Time ISS Live Telemetry Streamer (Mandatory Training Gated)",
                    "agent4": "AI & CFD Flame Visual Stimulation & Dynamics Simulation"
                },
                "iss_stream_online": iss_streamer.is_running
            })
            return

        # 2. Dynamic Variables
        if path == "/api/variables":
            agent_id = query.get("agent_id", [None])[0]
            only_pred = query.get("only_prediction", ["0"])[0] in ["1", "true"]
            vars_list = var_mgr.get_variables(agent_id=agent_id, only_prediction=only_pred)
            self._send_json_response({"variables": vars_list})
            return

        # 3. Complete 2-Way Front-End Contract (Input & Output Bridge)
        if path.startswith("/api/frontend-contract/"):
            agent_id = path.split("/")[-1]
            contract = var_mgr.generate_2way_frontend_contract(agent_id, base_url=public_base_url)
            self._send_json_response(contract)
            return

        # 4. Agent 2 LLM Bridge Configuration & Spec
        if path == "/api/settings/agent2-llm":
            cfg = llm_bridge.get_config()
            self._send_json_response(cfg)
            return

        if path == "/api/frontend-spec/agent2":
            spec = llm_bridge.generate_agent2_bridge_spec(base_url=public_base_url)
            self._send_json_response(spec)
            return

        # 5. Agent 3 Settings & Training Status
        if path == "/api/settings/agent3-iss":
            cfg = iss_streamer.get_config()
            self._send_json_response(cfg)
            return

        if path.startswith("/api/training-status/"):
            agent_id = path.split("/")[-1]
            status = data_ingestion.get_training_status(agent_id)
            self._send_json_response(status)
            return

        # 6. Agent 4 Combustion Materials
        if path == "/api/materials":
            mats = flame_engine.get_materials()
            self._send_json_response({"materials": mats})
            return

        # 7. Agent 3 ISS Current Snapshot
        if path == "/api/iss/current":
            snapshot = iss_streamer.get_latest_snapshot()
            self._send_json_response(snapshot)
            return

        # 8. Agent 3 Server-Sent Events (SSE) Live 1-Second Stream
        if path == "/api/stream/agent3":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._send_cors_headers()
            self.end_headers()

            last_tick = -1
            try:
                while True:
                    snapshot = iss_streamer.get_latest_snapshot()
                    cur_tick = snapshot.get("tick", 0)
                    if cur_tick != last_tick:
                        last_tick = cur_tick
                        payload = f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
                        self.wfile.write(payload.encode("utf-8"))
                        self.wfile.flush()
                    time.sleep(0.5)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        # 9. Static Web Dashboard Files
        if path in ["/", "/index.html"]:
            self._serve_static_file("index.html", "text/html; charset=utf-8")
            return
        elif path == "/styles.css":
            self._serve_static_file("styles.css", "text/css; charset=utf-8")
            return
        elif path == "/app.js":
            self._serve_static_file("app.js", "application/javascript; charset=utf-8")
            return

        self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Read JSON body
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            payload = {}

        # 1. Agent 1 Fire Risk Prediction
        if path == "/api/predict/agent1":
            user_vars = payload.get("variables", payload)
            result = ai_engine.predict("agent1", user_vars)
            self._send_json_response(result)
            return

        # 2. Agent 2 Grounded RAG Chatbot (Custom LLM Hook or Internal Safety Bot)
        if path == "/api/chat/agent2":
            user_msg = payload.get("message", "")
            result = llm_bridge.query_grounded_agent2(user_msg, safety_bot)
            self._send_json_response(result)
            return

        # 3. Agent 2 Save LLM Settings
        if path == "/api/settings/agent2-llm":
            saved = llm_bridge.save_config(payload)
            self._send_json_response({"success": True, "config": saved})
            return

        # 4. Agent 3 Save ISS Live API Settings
        if path == "/api/settings/agent3-iss":
            saved = iss_streamer.save_config(payload)
            self._send_json_response({"success": True, "config": saved})
            return

        # 5. Agent 4 AI & CFD Flame Visual Simulation
        if path == "/api/simulate/agent4":
            sim_vars = payload.get("variables", payload)
            result = flame_engine.simulate_flame(sim_vars)
            self._send_json_response(result)
            return

        # 6. Agent 4 Add or Update Combustion Material
        if path == "/api/materials":
            saved = flame_engine.add_or_update_material(payload)
            self._send_json_response({"success": True, "material": saved})
            return

        # 7. Dynamic Variable Management (Add / Update)
        if path == "/api/variables":
            updated_var = var_mgr.add_or_update_variable(payload)
            self._send_json_response({"success": True, "variable": updated_var})
            return

        # 8. Toggle Variable Prediction Status
        if path == "/api/variables/prediction_status":
            var_id = payload.get("id")
            is_active = bool(payload.get("is_active"))
            res = var_mgr.set_prediction_status(var_id, is_active)
            self._send_json_response({"success": res, "id": var_id, "is_active": is_active})
            return

        # 9. Universal Multi-Format Data Upload Endpoint (Agents 1, 2, 3, 4)
        if path.startswith("/api/upload/"):
            agent_id = path.split("/")[-1]
            try:
                batch_name = payload.get("batch_name", f"Batch_{int(time.time())}")
                format_type = payload.get("format_type", "json")
                raw_content = payload.get("content", "")
                user_vars = payload.get("user_defined_variables", [])
                filename = payload.get("filename", f"data.{format_type}")

                ingest_res = data_ingestion.ingest_data(
                    agent_id=agent_id,
                    batch_name=batch_name,
                    format_type=format_type,
                    file_content=raw_content,
                    user_defined_variables=user_vars,
                    filename=filename
                )

                if not ingest_res.get("success"):
                    self._send_json_response(ingest_res, status_code=400)
                    return

                all_records = ingest_res.get("all_records", [])
                discovered_vars = ingest_res.get("discovered_variables", [])

                # Auto-register all discovered variables in VariableManager
                for v_slug in discovered_vars:
                    if v_slug in ["risk_score", "target", "id", "timestamp", "date", "time", "_id"]:
                        continue
                    if not var_mgr.get_variable(v_slug):
                        pretty_name = v_slug.replace("_", " ").title()
                        var_mgr.add_or_update_variable({
                            "id": v_slug,
                            "name_ar": pretty_name,
                            "name_en": pretty_name,
                            "agent_id": agent_id if agent_id in ["agent1", "agent4"] else "global",
                            "data_type": "number",
                            "default_val": "0.0",
                            "is_active_for_prediction": 1
                        })

                # Agent-specific training and registration actions:
                train_res = None
                if agent_id in ["agent1", "agent3"] and all_records:
                    train_res = ai_engine.train_on_batch(agent_id, batch_name, all_records)
                    data_ingestion.set_training_status(
                        agent_id,
                        True,
                        len(all_records),
                        train_res.get("trained_features", discovered_vars)
                    )

                elif agent_id == "agent4" and all_records:
                    # Discover and add any new combustion materials
                    for r in all_records:
                        mat_name = r.get("fuel_material")
                        if mat_name and isinstance(mat_name, str):
                            mat_clean = mat_name.strip()
                            if mat_clean and not flame_engine.get_material(mat_clean):
                                flame_engine.add_or_update_material({
                                    "id": mat_clean,
                                    "name_ar": f"مادة {mat_clean}",
                                    "flame_temp_base": float(r.get("peak_temperature_k", 2000.0)),
                                    "sooting_propensity": 0.4,
                                    "limiting_oxygen_index": 16.0,
                                    "heat_of_combustion_mj_kg": 30.0,
                                    "description_ar": f"مادة احتراق تم استيرادها آلياً من دفعة {batch_name}"
                                })

                    # Auto-register condition variables for Agent 4
                    for v_slug in discovered_vars:
                        if v_slug in ["fuel_material", "flame_shape", "id"]:
                            continue
                        if not var_mgr.get_variable(v_slug):
                            var_mgr.add_or_update_variable({
                                "id": v_slug,
                                "name_ar": v_slug.replace("_", " ").title(),
                                "name_en": v_slug.replace("_", " ").title(),
                                "agent_id": "agent4",
                                "data_type": "number",
                                "default_val": "0.0",
                                "is_active_for_prediction": 1
                            })
                    data_ingestion.set_training_status(agent_id, True, len(all_records), discovered_vars)

                elif agent_id == "agent2":
                    data_ingestion.set_training_status(agent_id, True, len(all_records) or 1, ["documents_rag_indexed"])

                # Clean response (omit all_records to keep JSON payload lightweight)
                resp_payload = dict(ingest_res)
                resp_payload.pop("all_records", None)
                if train_res:
                    resp_payload["training_metrics"] = {
                        "accuracy_score": train_res.get("accuracy_score", 0.95),
                        "total_samples": train_res.get("total_samples", len(all_records)),
                        "feature_importances": train_res.get("feature_importances", {})
                    }

                self._send_json_response(resp_payload)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json_response({
                    "success": False,
                    "error": f"فشل أثناء معالجة البيانات: {str(e)}"
                }, status_code=400)
            return

        # 10. Model Training on Raw Batch
        if path.startswith("/api/train/"):
            agent_id = path.split("/")[-1]
            batch_name = payload.get("batch_name", f"Batch_{int(time.time())}")
            records = payload.get("records", [])
            train_res = ai_engine.train_on_batch(agent_id, batch_name, records)
            data_ingestion.set_training_status(agent_id, True, len(records), train_res.get("trained_features", []))
            self._send_json_response(train_res)
            return

        self.send_error(404, "Unknown API Route")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/variables/"):
            var_id = path.split("/")[-1]
            success = var_mgr.delete_variable(var_id)
            self._send_json_response({"success": success, "deleted_id": var_id})
            return

        if path.startswith("/api/materials/"):
            mat_id = path.split("/")[-1]
            success = flame_engine.delete_material(mat_id)
            self._send_json_response({"success": success, "deleted_material": mat_id})
            return

        self.send_error(404, "Endpoint Not Found")

    def _serve_static_file(self, filename: str, content_type: str):
        filepath = os.path.join(STATIC_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found.")
            return

        with open(filepath, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(content)


def run_server(port: int = 8500):
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, SpaceFireRequestHandler)
    print(f"🚀 NASA Space Fire AI Cloud Engine active on port {port}")
    print(f"🌐 Cloud / GitHub production ready: Access endpoints via HTTP & SSE.")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8500))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
