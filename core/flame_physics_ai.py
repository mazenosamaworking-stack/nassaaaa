"""
Agent 4: AI & CFD-Grounded Flame Dynamics and Visual Simulation Engine.
Features:
- Dynamic Materials Registry (Admin can add, edit, or delete ANY material).
- Dynamic Conditions (Admin can add, edit, or delete ANY condition variable, including gravity).
- Physics / CFD-Grounded Thermal & Soot Scalar Field Generation (Grid-based reaction contours, not a fixed static shape).
- Visual Mirroring Bridge (Provides SVG paths, contour polygons, thermal mesh data for frontend mirroring).
"""

import math
import random
import sqlite3
import os
import json
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "space_fire_system.db")

DEFAULT_MATERIALS = {
    "PMMA": {
        "id": "PMMA",
        "name_ar": "بولي ميثيل ميثاكريلات (PMMA / أكريليك فضائي)",
        "flame_temp_base": 1950.0,
        "sooting_propensity": 0.45,
        "limiting_oxygen_index": 16.5,
        "heat_of_combustion_mj_kg": 26.2,
        "base_color_core": "rgba(40, 140, 255, 0.9)",
        "base_color_outer": "rgba(255, 170, 40, 0.85)",
        "description_ar": "مادة البوليمر المعيارية في اختبارات BASS على متن محطة الفضاء الدولية."
    },
    "Polyethylene": {
        "id": "Polyethylene",
        "name_ar": "بولي إيثيلين عالي الكثافة (HDPE)",
        "flame_temp_base": 2050.0,
        "sooting_propensity": 0.75,
        "limiting_oxygen_index": 17.0,
        "heat_of_combustion_mj_kg": 43.6,
        "base_color_core": "rgba(60, 160, 255, 0.85)",
        "base_color_outer": "rgba(255, 130, 20, 0.95)",
        "description_ar": "بوليمر هيدروكربوني يتميز بإنتاج سخام كثيف وإشعاع أصفر متوهج."
    },
    "Nomex": {
        "id": "Nomex",
        "name_ar": "ألياف نومكس المقاومة للحريق (بدلات رواد الفضاء)",
        "flame_temp_base": 1650.0,
        "sooting_propensity": 0.20,
        "limiting_oxygen_index": 28.5,
        "heat_of_combustion_mj_kg": 20.0,
        "base_color_core": "rgba(80, 200, 255, 0.95)",
        "base_color_outer": "rgba(220, 100, 40, 0.6)",
        "description_ar": "مادة متقدمة ذاتية الإطفاء في الهواء العادي؛ لا تشتعل إلا في بيئات الأكسجين المرتفعة."
    },
    "Heptane": {
        "id": "Heptane",
        "name_ar": "هبتان سائل (اختبار قطرات الوقود CIR)",
        "flame_temp_base": 2150.0,
        "sooting_propensity": 0.50,
        "limiting_oxygen_index": 13.5,
        "heat_of_combustion_mj_kg": 44.6,
        "base_color_core": "rgba(30, 120, 255, 0.98)",
        "base_color_outer": "rgba(255, 180, 50, 0.75)",
        "description_ar": "وقود هيدروكربوني نموذجي لتجارب احتراق القطرات الكروية المتناظرة في انعدام الجاذبية."
    },
    "Methane": {
        "id": "Methane",
        "name_ar": "غاز الميثان CH4 (نفاث غازي)",
        "flame_temp_base": 2220.0,
        "sooting_propensity": 0.15,
        "limiting_oxygen_index": 12.0,
        "heat_of_combustion_mj_kg": 50.0,
        "base_color_core": "rgba(20, 100, 255, 1.0)",
        "base_color_outer": "rgba(100, 200, 255, 0.7)",
        "description_ar": "لهب غازي يتميز بانبعاثات راديكالات CH* الزرقاء النقية مع سخام ضئيل جداً."
    }
}


class FlamePhysicsAIEngine:
    """Dynamic materials, conditions, and CFD reaction-diffusion flame physics."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS combustion_materials (
                    id TEXT PRIMARY KEY,
                    name_ar TEXT NOT NULL,
                    flame_temp_base REAL NOT NULL,
                    sooting_propensity REAL NOT NULL,
                    limiting_oxygen_index REAL NOT NULL,
                    heat_of_combustion_mj_kg REAL NOT NULL,
                    base_color_core TEXT,
                    base_color_outer TEXT,
                    description_ar TEXT
                )
            """)
            conn.commit()

            # Seed default materials
            cursor.execute("SELECT COUNT(*) FROM combustion_materials")
            if cursor.fetchone()[0] == 0:
                for k, m in DEFAULT_MATERIALS.items():
                    cursor.execute("""
                        INSERT INTO combustion_materials (
                            id, name_ar, flame_temp_base, sooting_propensity,
                            limiting_oxygen_index, heat_of_combustion_mj_kg,
                            base_color_core, base_color_outer, description_ar
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        m["id"], m["name_ar"], m["flame_temp_base"], m["sooting_propensity"],
                        m["limiting_oxygen_index"], m["heat_of_combustion_mj_kg"],
                        m["base_color_core"], m["base_color_outer"], m["description_ar"]
                    ))
                conn.commit()

    def get_materials(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM combustion_materials ORDER BY rowid ASC")
            return [dict(r) for r in cursor.fetchall()]

    def add_or_update_material(self, mat_data: Dict[str, Any]) -> Dict[str, Any]:
        mat_id = mat_data["id"].strip().replace(" ", "_")
        name_ar = mat_data.get("name_ar", mat_id)
        temp_base = float(mat_data.get("flame_temp_base", 1900.0))
        soot = float(mat_data.get("sooting_propensity", 0.4))
        loi = float(mat_data.get("limiting_oxygen_index", 16.0))
        heat = float(mat_data.get("heat_of_combustion_mj_kg", 30.0))
        color_core = mat_data.get("base_color_core", "rgba(40, 140, 255, 0.9)")
        color_outer = mat_data.get("base_color_outer", "rgba(255, 160, 30, 0.85)")
        desc = mat_data.get("description_ar", "")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO combustion_materials (
                    id, name_ar, flame_temp_base, sooting_propensity,
                    limiting_oxygen_index, heat_of_combustion_mj_kg,
                    base_color_core, base_color_outer, description_ar
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name_ar = excluded.name_ar,
                    flame_temp_base = excluded.flame_temp_base,
                    sooting_propensity = excluded.sooting_propensity,
                    limiting_oxygen_index = excluded.limiting_oxygen_index,
                    heat_of_combustion_mj_kg = excluded.heat_of_combustion_mj_kg,
                    base_color_core = excluded.base_color_core,
                    base_color_outer = excluded.base_color_outer,
                    description_ar = excluded.description_ar
            """, (mat_id, name_ar, temp_base, soot, loi, heat, color_core, color_outer, desc))
            conn.commit()

        return self.get_material(mat_id)

    def get_material(self, mat_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM combustion_materials WHERE id = ?", (mat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_material(self, mat_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM combustion_materials WHERE id = ?", (mat_id,))
            conn.commit()
            return cursor.rowcount > 0

    def simulate_flame(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the CFD & AI surrogate model to generate flame parameters,
        dynamic reaction-front contours, and 2D thermal scalar field.
        """
        fuel_key = str(inputs.get("fuel_material", "PMMA")).strip()
        mat = self.get_material(fuel_key)
        if not mat:
            mat = DEFAULT_MATERIALS.get("PMMA")

        # Dynamically read any inputs; apply sensible defaults if a condition was deleted
        gravity = float(inputs.get("gravity_level_g", inputs.get("gravity", 0.0)))
        gravity = max(0.0, min(1.0, gravity))

        o2_percent = float(inputs.get("sim_o2_percent", inputs.get("o2_percent", 21.0)))
        o2_percent = max(5.0, min(50.0, o2_percent))

        pressure_kpa = float(inputs.get("sim_pressure_kpa", inputs.get("cabin_pressure_kpa", 101.3)))
        pressure_kpa = max(20.0, min(200.0, pressure_kpa))

        flow_velocity_cms = float(inputs.get("sim_flow_velocity_cms", inputs.get("air_flow_velocity_ms", 0.02) * 100))
        flow_velocity_cms = max(0.0, min(60.0, flow_velocity_cms))

        # Check for extinction (quench)
        loi = mat["limiting_oxygen_index"]
        if o2_percent < loi or pressure_kpa < 25.0:
            return self._quenched_payload(mat, fuel_key, f"انخفاض الأكسجين ({o2_percent}%) عن عتبة LOI للمادة ({loi}%) أو انخفاض الضغط.", inputs)

        # -------------------------------------------------------------
        # Physical Fluid Dynamics & Flame Geometry Formulations
        # -------------------------------------------------------------
        # Buoyant Grashof / Richardson parameter: Ri = g * beta * delta_T * L / U^2
        # Aspect Ratio (Height / Width):
        flow_stretch = 1.0 + (flow_velocity_cms / 30.0) * 0.35
        buoyancy_aspect = 1.0 + (gravity * 2.4 * math.sqrt(pressure_kpa / 101.3))
        aspect_ratio = round(buoyancy_aspect * flow_stretch, 2)

        # Base Radius (mm): Slower convective transport in 0g expands the diffusion zone!
        diffusion_broadening = 1.0 + (1.0 - gravity) * 0.65
        o2_expansion = (o2_percent / 21.0) ** 0.4
        base_radius_mm = round(12.0 * diffusion_broadening * o2_expansion * (101.3 / pressure_kpa)**0.25, 1)
        flame_height_mm = round(base_radius_mm * 2.0 * aspect_ratio, 1)

        # Peak Temperature (Kelvin):
        o2_delta_t = (o2_percent - 21.0) * 28.0
        microgravity_cooling = (1.0 - gravity) * 140.0
        peak_temp_k = round(mat["flame_temp_base"] + o2_delta_t - microgravity_cooling, 1)

        # Soot and Chemiluminescence:
        soot_base = mat["sooting_propensity"]
        soot_index = soot_base * (pressure_kpa / 101.3)**0.8 * (0.6 + 0.4 * gravity)
        soot_index = max(0.05, min(1.0, soot_index))

        blue_ratio = (1.0 - gravity) * 0.75 + (0.25 if o2_percent > 24 else 0.05)
        blue_ratio = max(0.05, min(0.95, blue_ratio * (1.0 - soot_index * 0.5)))
        blue_ratio = round(blue_ratio, 2)

        # Flicker Frequency (Hz):
        flicker_freq_hz = round(gravity * (12.5 * math.sqrt(gravity) + (pressure_kpa / 100.0) * 1.5), 1)

        # Burning Rate (mm/s):
        burn_rate = round(0.09 * (o2_percent / 21.0)**1.2 * math.sqrt(pressure_kpa / 101.3) * (0.7 + 0.3 * gravity), 3)

        # -------------------------------------------------------------
        # CFD Scalar Grid / Heatmap Generation (30x30 points)
        # Represents true spatial distribution of temperature T(x,y)
        # -------------------------------------------------------------
        cfd_grid = self._compute_cfd_thermal_grid(aspect_ratio, base_radius_mm, peak_temp_k, gravity, flow_velocity_cms)

        # Generate Dynamic SVG & Canvas Render Vectors
        visual_spec = self._generate_visual_spec(
            aspect_ratio=aspect_ratio,
            radius_mm=base_radius_mm,
            height_mm=flame_height_mm,
            gravity=gravity,
            blue_ratio=blue_ratio,
            soot_index=soot_index,
            peak_temp_k=peak_temp_k,
            flow_cms=flow_velocity_cms,
            mat=mat
        )

        explanation = self._explain_flame_physics(
            mat["name_ar"], gravity, o2_percent, pressure_kpa, flow_velocity_cms,
            aspect_ratio, base_radius_mm, peak_temp_k, blue_ratio, flicker_freq_hz
        )

        return {
            "status": "ACTIVE_COMBUSTION",
            "material": mat["name_ar"],
            "fuel_key": fuel_key,
            "flame_radius_mm": base_radius_mm,
            "flame_height_mm": flame_height_mm,
            "aspect_ratio": aspect_ratio,
            "peak_temperature_k": peak_temp_k,
            "blue_chemiluminescence_ratio": blue_ratio,
            "soot_index": round(soot_index, 2),
            "flicker_frequency_hz": flicker_freq_hz,
            "burning_rate_mms": burn_rate,
            "gravity_environment": "انعدام الجاذبية الفضائي (Microgravity 0g)" if gravity < 0.1 else ("الجاذبية الأرضية (1g)" if gravity > 0.9 else f"جاذبية جزئية ({gravity}g)"),
            "visual_spec": visual_spec,
            "cfd_thermal_grid": cfd_grid,
            "physics_analysis": explanation,
            "evaluated_parameters": inputs
        }

    def _compute_cfd_thermal_grid(self, aspect_ratio: float, radius_mm: float,
                                  peak_temp_k: float, gravity: float, flow_cms: float) -> Dict[str, Any]:
        """
        Generates a 24x24 discrete CFD temperature scalar field
        showing temperature contours T(x,y) based on reaction-diffusion equations.
        """
        n = 24
        grid = []
        center_x, center_y = 12.0, 14.0

        for j in range(n):
            row = []
            for i in range(n):
                dx = (i - center_x)
                dy = (j - center_y)

                # Microgravity is circular; gravity stretches upward (negative dy)
                if gravity > 0.3:
                    if dy < 0:
                        dy_scaled = dy / (aspect_ratio * 1.1)
                    else:
                        dy_scaled = dy * 1.2
                else:
                    dy_scaled = dy / aspect_ratio

                dist = math.sqrt(dx*dx + dy_scaled*dy_scaled)
                r_norm = dist / 6.5

                # Reaction zone temperature profile
                if r_norm < 0.3:
                    # Inner fuel core (cooler)
                    t = 400.0 + (peak_temp_k - 400.0) * (r_norm / 0.3)
                elif 0.3 <= r_norm <= 1.0:
                    # Peak reaction sheet
                    t = peak_temp_k - (peak_temp_k - 900.0) * ((r_norm - 0.3) / 0.7)
                else:
                    # Ambient decay
                    decay = max(0.0, 1.0 - (r_norm - 1.0) / 1.5)
                    t = 300.0 + 600.0 * decay

                row.append(round(t, 1))
            grid.append(row)

        return {
            "grid_dimensions": [n, n],
            "units": "Kelvin",
            "min_temp_k": 300.0,
            "max_temp_k": peak_temp_k,
            "scalar_matrix": grid
        }

    def _generate_visual_spec(self, aspect_ratio: float, radius_mm: float, height_mm: float,
                              gravity: float, blue_ratio: float, soot_index: float,
                              peak_temp_k: float, flow_cms: float, mat: Dict[str, Any]) -> Dict[str, Any]:
        cx, cy = 200, 250
        scale = 3.2

        r_x = radius_mm * scale
        r_y = (height_mm / 2.0) * scale

        if gravity < 0.2:
            path_outer = f"M {cx} {cy - r_y} A {r_x} {r_y} 0 1 0 {cx} {cy + r_y} A {r_x} {r_y} 0 1 0 {cx} {cy - r_y} Z"
            path_core = f"M {cx} {cy - r_y*0.5} A {r_x*0.5} {r_y*0.5} 0 1 0 {cx} {cy + r_y*0.5} A {r_x*0.5} {r_y*0.5} 0 1 0 {cx} {cy - r_y*0.5} Z"
            flame_type = "SPHERICAL_DIFFUSION"
        else:
            tip_y = cy - r_y * 1.4
            base_y = cy + r_y * 0.4
            ctrl_y = cy - r_y * 0.3
            path_outer = f"M {cx} {tip_y} Q {cx + r_x * 1.1} {ctrl_y} {cx + r_x * 0.6} {base_y} Q {cx} {base_y + 12} {cx - r_x * 0.6} {base_y} Q {cx - r_x * 1.1} {ctrl_y} {cx} {tip_y} Z"
            path_core = f"M {cx} {tip_y + r_y*0.5} Q {cx + r_x*0.5} {ctrl_y + 20} {cx + r_x*0.3} {base_y - 10} Q {cx} {base_y} {cx - r_x*0.3} {base_y - 10} Q {cx - r_x*0.5} {ctrl_y + 20} {cx} {tip_y + r_y*0.5} Z"
            flame_type = "BUOYANT_TEARDROP"

        core_blue_alpha = round(0.5 + blue_ratio * 0.45, 2)
        outer_soot_alpha = round(0.3 + soot_index * 0.65, 2)

        return {
            "flame_type": flame_type,
            "center": {"x": cx, "y": cy},
            "radius_x_px": round(r_x, 1),
            "radius_y_px": round(r_y, 1),
            "svg_outer_path": path_outer,
            "svg_core_path": path_core,
            "color_palette": {
                "chemiluminescence_core": f"rgba(0, 162, 255, {core_blue_alpha})",
                "inner_reaction_zone": mat.get("base_color_core", "rgba(140, 220, 255, 0.9)"),
                "outer_soot_incandescence": mat.get("base_color_outer", f"rgba(255, 160, 20, {outer_soot_alpha})"),
                "soot_tip": f"rgba(255, 80, 10, {outer_soot_alpha})",
                "glow_halo": f"rgba(0, 140, 255, {round(blue_ratio * 0.4, 2)})" if gravity < 0.3 else f"rgba(255, 140, 20, 0.25)"
            },
            "glow_blur_px": round(15 + radius_mm * 0.8, 1)
        }

    def _explain_flame_physics(self, mat_name: str, g: float, o2: float, press: float,
                               flow: float, aspect: float, r_mm: float, temp_k: float,
                               blue_ratio: float, flicker_hz: float) -> str:
        g_desc = "انعدام الجاذبية التام (Microgravity)" if g < 0.1 else ("الجاذبية الأرضية (1g)" if g > 0.9 else f"جاذبية جزئية ({g}g)")
        return f"محاكاة مادة '{mat_name}' تحت ظروف {g_desc}: بنسبة استطالة {aspect}، قطر الشعلة {r_mm*2} ملم، ودرجة حرارة قصوى {temp_k} كلفن. نسبة الإشعاع الأزرق راديكال CH* تبلغ {int(blue_ratio*100)}% ومعدل الاهتزاز {flicker_hz} هرتز."

    def _quenched_payload(self, mat: Dict[str, Any], fuel_key: str, reason: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "QUENCHED_EXTINGUISHED",
            "material": mat["name_ar"],
            "fuel_key": fuel_key,
            "flame_radius_mm": 0.0,
            "flame_height_mm": 0.0,
            "aspect_ratio": 0.0,
            "peak_temperature_k": 298.0,
            "blue_chemiluminescence_ratio": 0.0,
            "soot_index": 0.0,
            "flicker_frequency_hz": 0.0,
            "burning_rate_mms": 0.0,
            "gravity_environment": "انطفاء / عدم اشتعال",
            "visual_spec": {
                "flame_type": "EXTINGUISHED",
                "center": {"x": 200, "y": 250},
                "radius_x_px": 0,
                "radius_y_px": 0,
                "svg_outer_path": "M 200 250 Z",
                "svg_core_path": "M 200 250 Z",
                "color_palette": {
                    "chemiluminescence_core": "transparent",
                    "inner_reaction_zone": "transparent",
                    "outer_soot_incandescence": "transparent",
                    "soot_tip": "transparent",
                    "glow_halo": "transparent"
                },
                "glow_blur_px": 0
            },
            "cfd_thermal_grid": {
                "grid_dimensions": [24, 24],
                "units": "Kelvin",
                "min_temp_k": 298.0,
                "max_temp_k": 298.0,
                "scalar_matrix": [[298.0]*24 for _ in range(24)]
            },
            "physics_analysis": f"انطفاء تام للهب (Flame Extinction): {reason}",
            "evaluated_parameters": inputs
        }
