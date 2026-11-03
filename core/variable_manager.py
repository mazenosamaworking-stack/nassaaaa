"""
Dynamic Variable & 2-Way Front-End Mapping Contract Manager.
Manages dynamic custom fields across all agents and generates:
1. Input Bridge (How the frontend sends each variable to the server).
2. Output Bridge (How the frontend reads and binds each predicted output metric).
"""

import json
import sqlite3
import os
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "space_fire_system.db")

DEFAULT_VARIABLES = [
    {
        "id": "o2_percent",
        "name_ar": "نسبة الأكسجين O2",
        "name_en": "Oxygen Concentration",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "%",
        "min_val": 10.0,
        "max_val": 40.0,
        "default_val": 21.0,
        "description": "نسبة تركيز غاز الأكسجين في بيئة المركبة / المحطة",
        "is_active_for_prediction": 1,
        "importance_weight": 1.5
    },
    {
        "id": "cabin_pressure_kpa",
        "name_ar": "ضغط المقصورة",
        "name_en": "Cabin Pressure",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "kPa",
        "min_val": 50.0,
        "max_val": 120.0,
        "default_val": 101.3,
        "description": "الضغط الجوي الكلي داخل مقصورة المركبة الفضائية",
        "is_active_for_prediction": 1,
        "importance_weight": 1.2
    },
    {
        "id": "co2_percent",
        "name_ar": "نسبة ثاني أكسيد الكربون CO2",
        "name_en": "Carbon Dioxide Concentration",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "%",
        "min_val": 0.0,
        "max_val": 5.0,
        "default_val": 0.4,
        "description": "تركيز غاز CO2 في هواء المقصورة",
        "is_active_for_prediction": 1,
        "importance_weight": 1.1
    },
    {
        "id": "ambient_temp_c",
        "name_ar": "درجة حرارة البيئة المحيطة",
        "name_en": "Ambient Temperature",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "°C",
        "min_val": 10.0,
        "max_val": 80.0,
        "default_val": 23.5,
        "description": "درجة حرارة الهواء داخل وحدة المركبة",
        "is_active_for_prediction": 1,
        "importance_weight": 1.3
    },
    {
        "id": "air_flow_velocity_ms",
        "name_ar": "سرعة تيار التهوية الهوائية",
        "name_en": "Ventilation Air Velocity",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "m/s",
        "min_val": 0.0,
        "max_val": 1.5,
        "default_val": 0.12,
        "description": "سرعة حركة الهواء الناتجة عن مراوح التهوية القسرية في انعدام الجاذبية",
        "is_active_for_prediction": 1,
        "importance_weight": 1.4
    },
    {
        "id": "material_flammability_index",
        "name_ar": "مؤشر قابلية المادة للاشتعال (FPI)",
        "name_en": "Flammability Propensity Index",
        "agent_id": "agent1",
        "data_type": "number",
        "unit": "index",
        "min_val": 0.1,
        "max_val": 5.0,
        "default_val": 1.0,
        "description": "مؤشر ناسا لقابلية المواد للاشتعال والانتشار الحراري",
        "is_active_for_prediction": 1,
        "importance_weight": 1.4
    },
    # Agent 4 Condition Variables
    {
        "id": "gravity_level_g",
        "name_ar": "مستوى الجاذبية (Gravity g)",
        "name_en": "Gravity Level",
        "agent_id": "agent4",
        "data_type": "number",
        "unit": "g",
        "min_val": 0.0,
        "max_val": 1.0,
        "default_val": 0.0,
        "description": "مستوى الجاذبية (0g لانعدام الجاذبية في محطة ISS أو 1g للأرض)",
        "is_active_for_prediction": 1,
        "importance_weight": 1.8
    },
    {
        "id": "sim_o2_percent",
        "name_ar": "نسبة الأكسجين للمحاكاة",
        "name_en": "Simulation O2 %",
        "agent_id": "agent4",
        "data_type": "number",
        "unit": "%",
        "min_val": 12.0,
        "max_val": 45.0,
        "default_val": 21.0,
        "description": "تركيز الأكسجين المؤثر على حركية اللهب وسرعة الاحتراق",
        "is_active_for_prediction": 1,
        "importance_weight": 1.5
    },
    {
        "id": "sim_pressure_kpa",
        "name_ar": "الضغط المحيط للمحاكاة",
        "name_en": "Simulation Ambient Pressure",
        "agent_id": "agent4",
        "data_type": "number",
        "unit": "kPa",
        "min_val": 30.0,
        "max_val": 150.0,
        "default_val": 101.3,
        "description": "الضغط المحيط بحجرة الاحتراق الفضائية",
        "is_active_for_prediction": 1,
        "importance_weight": 1.3
    },
    {
        "id": "sim_flow_velocity_cms",
        "name_ar": "سرعة سريان التدفق الهوائي",
        "name_en": "Flow Velocity",
        "agent_id": "agent4",
        "data_type": "number",
        "unit": "cm/s",
        "min_val": 0.0,
        "max_val": 50.0,
        "default_val": 2.0,
        "description": "سرعة انجراف الهواء حول شعلة اللهب",
        "is_active_for_prediction": 1,
        "importance_weight": 1.4
    }
]


class VariableManager:
    """Manages custom variables and 2-way front-end contracts."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS variables (
                    id TEXT PRIMARY KEY,
                    name_ar TEXT NOT NULL,
                    name_en TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    unit TEXT,
                    min_val REAL,
                    max_val REAL,
                    default_val TEXT,
                    description TEXT,
                    is_active_for_prediction INTEGER DEFAULT 1,
                    importance_weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM variables")
            if cursor.fetchone()[0] == 0:
                for v in DEFAULT_VARIABLES:
                    cursor.execute("""
                        INSERT INTO variables (
                            id, name_ar, name_en, agent_id, data_type, unit,
                            min_val, max_val, default_val, description,
                            is_active_for_prediction, importance_weight
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        v["id"], v["name_ar"], v["name_en"], v["agent_id"],
                        v["data_type"], v["unit"], v["min_val"], v["max_val"],
                        str(v["default_val"]), v["description"],
                        v["is_active_for_prediction"], v["importance_weight"]
                    ))
                conn.commit()

    def get_variables(self, agent_id: Optional[str] = None, only_prediction: bool = False) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM variables WHERE 1=1"
            params = []
            if agent_id:
                query += " AND (agent_id = ? OR agent_id = 'global')"
                params.append(agent_id)
            if only_prediction:
                query += " AND is_active_for_prediction = 1"
            query += " ORDER BY rowid ASC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def add_or_update_variable(self, var_data: Dict[str, Any]) -> Dict[str, Any]:
        var_id = var_data["id"].strip().lower().replace(" ", "_")
        name_ar = var_data.get("name_ar") or var_id
        name_en = var_data.get("name_en") or var_id
        agent_id = var_data.get("agent_id", "agent1")
        data_type = var_data.get("data_type", "number")
        unit = var_data.get("unit", "")
        min_val = float(var_data.get("min_val", 0.0))
        max_val = float(var_data.get("max_val", 100.0))
        default_val = str(var_data.get("default_val", "0"))
        description = var_data.get("description", "")
        is_active = int(var_data.get("is_active_for_prediction", 1))
        weight = float(var_data.get("importance_weight", 1.0))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO variables (
                    id, name_ar, name_en, agent_id, data_type, unit,
                    min_val, max_val, default_val, description,
                    is_active_for_prediction, importance_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name_ar = excluded.name_ar,
                    name_en = excluded.name_en,
                    agent_id = excluded.agent_id,
                    data_type = excluded.data_type,
                    unit = excluded.unit,
                    min_val = excluded.min_val,
                    max_val = excluded.max_val,
                    default_val = excluded.default_val,
                    description = excluded.description,
                    is_active_for_prediction = excluded.is_active_for_prediction,
                    importance_weight = excluded.importance_weight
            """, (
                var_id, name_ar, name_en, agent_id, data_type, unit,
                min_val, max_val, default_val, description, is_active, weight
            ))
            conn.commit()

        return self.get_variable(var_id)

    def get_variable(self, var_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM variables WHERE id = ?", (var_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_variable(self, var_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM variables WHERE id = ?", (var_id,))
            conn.commit()
            return cursor.rowcount > 0

    def set_prediction_status(self, var_id: str, is_active: bool) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE variables SET is_active_for_prediction = ? WHERE id = ?",
                (1 if is_active else 0, var_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def generate_2way_frontend_contract(self, agent_id: str, base_url: str = "http://localhost:8500") -> Dict[str, Any]:
        """
        Generates complete 2-way Front-End Contract:
        1. Input Bridge: How to send each variable from the frontend.
        2. Output Bridge: How to extract and bind the predicted result to the frontend.
        """
        vars_list = self.get_variables(agent_id=agent_id, only_prediction=True)
        endpoint = f"{base_url}/api/predict/{agent_id}" if agent_id != "agent4" else f"{base_url}/api/simulate/agent4"

        input_fields = []
        sample_request_vars = {}

        for v in vars_list:
            def_val = float(v["default_val"]) if v["data_type"] == "number" else v["default_val"]
            sample_request_vars[v["id"]] = def_val

            input_fields.append({
                "field_id": v["id"],
                "label_ar": v["name_ar"],
                "data_type": v["data_type"],
                "unit": v["unit"],
                "min": v["min_val"],
                "max": v["max_val"],
                "default": def_val,
                "json_key": f"variables.{v['id']}",
                "html_snippet": f'<input type="{"number" if v["data_type"] == "number" else "text"}" id="input_{v["id"]}" name="{v["id"]}" value="{def_val}" />',
                "js_read_snippet": f'const {v["id"]}_val = document.getElementById("input_{v["id"]}").value;'
            })

        # Define Output Bridge mappings
        if agent_id in ["agent1", "agent3"]:
            output_mappings = [
                {
                    "target_metric": "نسبة حدوث الحريق",
                    "json_response_path": "data.fire_probability_percent",
                    "type": "number (0 - 100)",
                    "frontend_binding_example": 'document.getElementById("risk_gauge").innerText = `${data.fire_probability_percent}%`;'
                },
                {
                    "target_metric": "درجة الخطورة",
                    "json_response_path": "data.hazard_level",
                    "type": "string (آمن / متوسط / مرتفع / حرج)",
                    "frontend_binding_example": 'document.getElementById("hazard_badge").innerText = data.hazard_level;'
                },
                {
                    "target_metric": "لون الخطر",
                    "json_response_path": "data.hazard_color",
                    "type": "string hex/rgb",
                    "frontend_binding_example": 'document.getElementById("hazard_badge").style.borderColor = data.hazard_color;'
                },
                {
                    "target_metric": "وصف الـ AI للحالة",
                    "json_response_path": "data.description",
                    "type": "string",
                    "frontend_binding_example": 'document.getElementById("ai_diagnosis_text").innerText = data.description;'
                },
                {
                    "target_metric": "أثر المتغيرات المدخلة في النتيجة",
                    "json_response_path": "data.feature_contributions",
                    "type": "object { field_id: delta_percent }",
                    "frontend_binding_example": 'console.log("تأثير المتغيرات:", data.feature_contributions);'
                }
            ]
        elif agent_id == "agent4":
            output_mappings = [
                {
                    "target_metric": "مسار رسم اللهب الخارجي (SVG)",
                    "json_response_path": "data.visual_spec.svg_outer_path",
                    "type": "string (SVG path data M... Z)",
                    "frontend_binding_example": 'document.getElementById("flame_svg_outer").setAttribute("d", data.visual_spec.svg_outer_path);'
                },
                {
                    "target_metric": "مسار نواة اللهب التفاعلية (SVG)",
                    "json_response_path": "data.visual_spec.svg_core_path",
                    "type": "string (SVG path data)",
                    "frontend_binding_example": 'document.getElementById("flame_svg_core").setAttribute("d", data.visual_spec.svg_core_path);'
                },
                {
                    "target_metric": "مصفوفة الحقل الحراري CFD Scalar Grid",
                    "json_response_path": "data.cfd_thermal_grid.scalar_matrix",
                    "type": "2D Array (24x24 temperatures in Kelvin)",
                    "frontend_binding_example": 'renderHeatmapCanvas(data.cfd_thermal_grid.scalar_matrix);'
                },
                {
                    "target_metric": "ألوان الشعلة الفيزيائية",
                    "json_response_path": "data.visual_spec.color_palette",
                    "type": "object { chemiluminescence_core, outer_soot_incandescence, glow_halo }",
                    "frontend_binding_example": 'const colors = data.visual_spec.color_palette;'
                },
                {
                    "target_metric": "نسبة استطالة اللهب والتردد",
                    "json_response_path": "data.aspect_ratio / data.flicker_frequency_hz",
                    "type": "numbers",
                    "frontend_binding_example": 'console.log(`استطالة: ${data.aspect_ratio}, اهتزاز: ${data.flicker_frequency_hz} Hz`);'
                }
            ]
        else:
            output_mappings = []

        full_fetch_code = f"""// كود الربط الكامل ثنائي الاتجاه (2-Way Binding) لـ {agent_id.upper()}
async function execute{agent_id.capitalize()}Call() {{
  // 1. تجميع المدخلات من الخانات المعرفة في الفرونت إند:
  const inputVariables = {{
{chr(10).join([f"    '{f['field_id']}': parseFloat(document.getElementById('input_{f['field_id']}').value)," for f in input_fields if f['data_type'] == 'number'])}
  }};

  // 2. إرسال الطلب إلى السيرفر (العقل):
  const response = await fetch('{endpoint}', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ variables: inputVariables }})
  }});
  const data = await response.json();

  // 3. ربط المخرجات فوراً بعناصر واجهتك:
{chr(10).join([f"  // {m['target_metric']}:{chr(10)}  {m['frontend_binding_example']}" for m in output_mappings])}
}}"""

        return {
            "agent_id": agent_id,
            "endpoint_url": endpoint,
            "http_method": "POST",
            "input_bridge": {
                "fields": input_fields,
                "sample_request_body": {"variables": sample_request_vars}
            },
            "output_bridge": {
                "mappings": output_mappings
            },
            "complete_fetch_snippet": full_fetch_code
        }
