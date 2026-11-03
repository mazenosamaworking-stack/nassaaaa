"""
Generates realistic, scientifically calibrated mock datasets for all 4 NASA Space Fire Agents.
Saves data in multiple formats (CSV, JSON, and Text/Manuals) inside sample_datasets/.
"""

import os
import json
import csv
import random
import math
from datetime import datetime, timedelta

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_datasets")
os.makedirs(DATASET_DIR, exist_ok=True)

random.seed(42)

# ==============================================================================
# 1. AGENT 1: NASA Spacecraft Fire Risk Prediction Dataset (150 rows)
# Includes heterogeneous variables: O2 %, Pressure, CO2 %, Temp, Flow, Wire Temp, Coolant Pressure
# ==============================================================================
print("Generating Agent 1 Data...")
agent1_rows = []
for i in range(160):
    o2 = round(random.uniform(15.0, 35.0), 2)
    pressure = round(random.uniform(65.0, 115.0), 1)
    co2 = round(random.uniform(0.15, 3.5), 2)
    temp = round(random.uniform(18.0, 70.0), 1)
    flow = round(random.uniform(0.01, 0.95), 3)
    fpi = round(random.uniform(0.8, 4.2), 2)
    wire_temp = round(random.uniform(22.0, 140.0), 1)
    coolant_press = round(random.uniform(120.0, 310.0), 1)

    # Physics-grounded risk score calculation
    o2_factor = max(0.0, (o2 - 18.0) / 10.0) ** 1.7 * 26.0
    temp_factor = max(0.0, (temp - 24.0) / 30.0) * 20.0
    wire_factor = max(0.0, (wire_temp - 60.0) / 40.0) * 24.0
    flow_factor = 14.0 if 0.08 <= flow <= 0.45 else 4.0
    co2_suppress = min(12.0, co2 * 4.0)
    mat_factor = (fpi - 1.0) * 10.0

    risk = 6.0 + o2_factor + temp_factor + wire_factor + flow_factor + mat_factor - co2_suppress
    risk += random.gauss(0, 2.5)
    risk = round(max(2.0, min(99.0, risk)), 1)

    row = {
        "id": i + 1,
        "o2_percent": o2,
        "cabin_pressure_kpa": pressure,
        "co2_percent": co2,
        "ambient_temp_c": temp,
        "air_flow_velocity_ms": flow,
        "material_flammability_index": fpi,
        "wire_temp_c": wire_temp,
        "coolant_pressure_kpa": coolant_press,
        "risk_score": risk
    }
    agent1_rows.append(row)

# Save Agent 1 CSV & JSON
a1_csv = os.path.join(DATASET_DIR, "agent1_fire_risk_data.csv")
with open(a1_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(agent1_rows[0].keys()))
    writer.writeheader()
    writer.writerows(agent1_rows)

a1_json = os.path.join(DATASET_DIR, "agent1_fire_risk_data.json")
with open(a1_json, "w", encoding="utf-8") as f:
    json.dump(agent1_rows, f, indent=2, ensure_ascii=False)

print(f"  -> Agent 1: Saved {len(agent1_rows)} rows to CSV and JSON.")


# ==============================================================================
# 2. AGENT 2: NASA Spaceflight Emergency Safety Protocols & Knowledge Base
# Text documents for RAG (Incident post-mortems, Flight rules, and Emergency SOPs)
# ==============================================================================
print("Generating Agent 2 Data...")
agent2_text = """NASA SP-2024-ECLSS: بروتوكولات وإجراءات طوارئ الحرائق والأعطال الحرارية لمركبات الفضاء ومحطة ISS

القسم 1: تشخيص وإجراءات أعطال التفريغ الكهربائي (Electrical Arcing & Wire Degradation)
- الوصف الفني: يحدث القوس الكهربائي عند انهيار العزل البوليمري (Teflon / Kapton) نتيجة اهتزازات الإطلاق أو الحمل الزائد الموضعي.
- المؤشرات التشخيصية: انبعاث دخان أسود خفيف، رائحة شياط بلاستيكية حادة، ومضات شرر متقطعة خلف ألواح قواطع التوزيع (RPCM / Avionics Bay).
- إجراءات السلامة الإلزامية:
  1. ارتداء أجهزة التنفس المحمولة (PBA / PBE Mask) لجميع أفراد الطاقم خلال 45 ثانية لمنع استنشاق حمض الهيدروفلوريك (HF) وأول أكسيد الكربون.
  2. فتح قواطع التوزيع وفصل التغذية الكهربائية (Depower Avionics Rack) فوراً لعزل مصدر الطاقة الحرارية.
  3. إيقاف صمامات التهوية القسرية للمقصورة لعزل انتشار الدخان ومحاصرة الأكسجين.
  4. استخدام طفاية الرذاذ المائي الدقيق (Fine Water Mist) المعزولة كهربائياً حتى 1000 فولت، أو طفاية CO2 في الحجرات المغلقة.

القسم 2: بروتوكول الانفلات الحراري لبطاريات الليثيوم (Lithium-Ion Battery Thermal Runaway)
- الوصف الفني: قصر دائرة داخلي ميكروي في خلايا الليثيوم يولد تفاعلاً طارداً للحرارة لا يحتاج أكسجين خارجي، مصحوباً بفرقعة وتصاعد غازات هيدروكربونية ملتهبة.
- المؤشرات التشخيصية: انتفاخ غلاف حزمة البطارية، صوت فرقعة متتابع، حرارة سطحية تتجاوز 120°C، ودخان أبيض كثيف.
- إجراءات السلامة الإلزامية:
  1. إعلان طوارئ حريق من الدرجة الأولى (Class-1 Fire Emergency).
  2. استخدام طفاية الماء الدقيق لكسر التفاعل الذاتي عبر التبريد المائي المستمر (Water Cooling). لا تستخدم غاز الهالون لأنه لا يبرد خلايا الليثيوم الداخلية.
  3. نقل حزمة البطارية فور احتوائها إلى كيس الاحتواء الحراري المقاوم للانفجار (Thermal Containment Bag).
  4. عزل الحزمة في وحدة معادلة الضغط (Airlock) إذا تعذر كبح الانبعاثات، وتشغيل نظام تنقية الغازات السامة TCCS بأقصى تدفق.

القسم 3: احتكاك محامل مراوح التهوية (ECLSS Ventilation Bearing Friction)
- الوصف الفني: تآكل محامل المحركات الكهربائية (Bearing Seizure) يولد حرارة احتكاك هائلة تتجمع موضعياً لانعدام تيارات الحمل الطبيعي في انعدام الجاذبية.
- المؤشرات التشخيصية: صوت صرير معدني عالي التردد، اهتزاز في مجرى الهواء، ارتفاع حرارة هيكل المروحة عن 85°C.
- إجراءات السلامة الإلزامية:
  1. إيقاف تشغيل مروحة التهوية المتضررة فوراً من لوحة تحكم ECLSS لمنع استمرار التوليد الحراري.
  2. غلق بوابات العزل (Isolation Dampers) لمجرى الهواء لمنع انتقال الحرارة لباقي الأقسام.
  3. قياس درجة حرارة المحرك بمسبار الأشعة تحت الحمراء حتى تنخفض تحت 50°C.
  4. تحويل تدوير الهواء للخط الاحتياطي المكرر (Redundant Air Loop).

القسم 4: تسريب خطوط الأكسجين عالي الضغط (Oxygen Micro-Leak & Flash Combustion)
- الوصف الفني: تسريب موضعي للأكسجين بنقاء > 99% يخفض طاقة التنشيط للاشتعال إلى جزء ضئيل، مما يجعل أي احتكاك بسيط يؤدي إلى وميض ناري فوري.
- المؤشرات التشخيصية: انخفاض ضغط الخط في التيليميتري، توهج أزرق نقي هادئ حول الصمامات، ارتفاع قراءة حساس O2 الموضعي فوق 25%.
- إجراءات السلامة الإلزامية:
  1. إغلاق صمامات عزل الأكسجين الرئيسية (Main O2 Isolation Valves) يدوياً وآلياً.
  2. حظر تشغيل أو فصل أي أجهزة كهربائية لتجنب الشرارات الثانوية.
  3. إخلاء الوحدة فوراً وإغلاق كوة الضغط (Hatch) لمنع انتقال الغازات إلى باقي وحدات المحطة.
  4. مراقبة تراجع نسبة الأكسجين حتى تعود للنطاق الآمن دون 21.5%.
"""

a2_txt = os.path.join(DATASET_DIR, "agent2_safety_emergency_manuals.txt")
with open(a2_txt, "w", encoding="utf-8") as f:
    f.write(agent2_text)

# Also create structured JSON chunks for Agent 2 RAG
agent2_json = [
    {
        "id": "SOP-ELEC-01",
        "title": "قوس تفريغ كهربائي وتلف العزل (Electrical Arcing)",
        "subsystem": "نظام توزيع الطاقة EPS",
        "symptoms": "دخان أسود خفيف، شرر متكرر، رائحة بلاستيك محترق",
        "root_cause": "انهيار العزل البوليمري للأسلاك نتيجة حمل تيار زائد أو اهتزاز ميكانيكي",
        "immediate_actions": [
            "ارتداء قناع التنفس PBA خلال 45 ثانية لحماية الرئتين من غاز HF السام",
            "فصل قاطع الدائرة وحرمان الحجرة من الطاقة (Depower Rack)",
            "إغلاق فتحات التهوية لمجرى الهواء لمحاصرة الدخان",
            "استخدام طفاية الرذاذ المائي الدقيق المعزول كهربائياً"
        ]
    },
    {
        "id": "SOP-BATT-02",
        "title": "انفلات حراري في بطاريات الليثيوم (Lithium-Ion Runaway)",
        "subsystem": "وحدات تخزين الطاقة المحمولة",
        "symptoms": "فرقعة، انتفاخ الحزمة، حرارة تفوق 120 مئوية، دخان أبيض",
        "root_cause": "قصر دائرة داخلي يسبب تفاعلاً ذاتياً طارداً للحرارة لا يحتاج أكسجيناً خارجياً",
        "immediate_actions": [
            "إعلان طوارئ حريق من الدرجة الأولى وارتداء أقنعة التنفس لجميع الرواد",
            "التبريد المستمر بطفاية الرذاذ المائي لكسر السلسلة الحرارية الداخلية",
            "وضع حزمة البطارية في كيس الاحتواء الحراري المقاوم للانفجار",
            "عزل الوحدة في غرفة معادلة الضغط Airlock وتشغيل TCCS بأقصى تدفق"
        ]
    },
    {
        "id": "SOP-VENT-03",
        "title": "احتكاك محامل مروحة التهوية (ECLSS Fan Friction)",
        "subsystem": "نظام دعم الحياة والتحكم البيئي",
        "symptoms": "صرير معدني، اهتزاز في مجرى الهواء، حرارة مفرطة في الغلاف",
        "root_cause": "تآكل وتصلب المحامل الميكانيكية للمروحة وتراكم الحرارة الموضعية",
        "immediate_actions": [
            "إيقاف مروحة التهوية فوراً من لوحة تحكم ECLSS لقطع التوليد الحراري",
            "إغلاق بوابات العزل الدائرية للمجرى لمنع انتقال الغازات الساخنة",
            "فحص الحرارة بالأشعة تحت الحمراء والتأكد من انخفاضها تحت 50 مئوية",
            "التحويل لمروحة الخط الهوائي الاحتياطي المكرر Redundant Loop"
        ]
    },
    {
        "id": "SOP-O2-04",
        "title": "تسريب خطوط الأكسجين عالي الضغط (Oxygen Micro-Leak)",
        "subsystem": "خطوط إمداد الأكسجين عالي الضغط",
        "symptoms": "توهج أزرق نقي، قراءة O2 فوق 25%، هبوط ضغط الأنابيب",
        "root_cause": "تسريب موضعي لغاز O2 النقي يرفع القابلية الكيميائية للاشتعال الفوري",
        "immediate_actions": [
            "إغلاق صمامات عزل الأكسجين الرئيسية يدوياً وآلياً على الفور",
            "منع الضغط على أي مفاتيح كهربائية لتفادي الشحنات الساكنة",
            "إخلاء الوحدة وإغلاق كوة الضغط لمنع انتقال الغازات لباقي المحطة",
            "مراقبة تراجع نسبة الأكسجين حتى عودتها للنطاق الطبيعي دون 21.5%"
        ]
    }
]

a2_json_file = os.path.join(DATASET_DIR, "agent2_incident_reports.json")
with open(a2_json_file, "w", encoding="utf-8") as f:
    json.dump(agent2_json, f, indent=2, ensure_ascii=False)

print("  -> Agent 2: Saved safety emergency manuals (TXT and JSON).")


# ==============================================================================
# 3. AGENT 3: ISS ECLSS Live Telemetry Sensor Dataset (200 records)
# Real orbital parameters & ECLSS atmospheric sensors (Destiny, Columbus, Kibo)
# ==============================================================================
print("Generating Agent 3 Data...")
base_time = datetime.utcnow() - timedelta(minutes=200)
agent3_rows = []

for i in range(200):
    t = base_time + timedelta(seconds=i * 60)
    orbit_angle = (i * 0.04) % (2 * math.pi)
    lat = round(51.6 * math.sin(orbit_angle), 4)
    lon = round(-180.0 + (i * 3.6) % 360.0, 4)
    alt = round(418.0 + 0.4 * math.sin(orbit_angle * 2), 2)
    speed = round(27600.0 + 15.0 * math.cos(orbit_angle), 1)

    # Periodic slight fluctuation in ISS atmospheric telemetry
    is_anomaly = 140 <= i <= 155
    o2 = round(21.2 + (2.5 if is_anomaly else random.uniform(-0.15, 0.15)), 2)
    pressure = round(101.3 + (1.2 if is_anomaly else random.uniform(-0.25, 0.25)), 2)
    co2 = round(0.35 + (0.45 if is_anomaly else random.uniform(-0.03, 0.03)), 3)
    temp = round(22.5 + (4.8 if is_anomaly else random.uniform(-0.3, 0.3)), 2)
    flow = round(0.12 + random.uniform(-0.01, 0.01), 3)

    smoke_destiny = round(0.08 if is_anomaly else random.uniform(0.02, 0.05), 3)
    smoke_columbus = round(0.06 if is_anomaly else random.uniform(0.01, 0.04), 3)

    # Fire risk calibrated score
    risk = 8.0 + (o2 - 20.9) * 9.0 + max(0.0, temp - 23.0) * 4.5
    if is_anomaly:
        risk += 35.0
    risk = round(max(5.0, min(95.0, risk)), 1)

    row = {
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latitude": lat,
        "longitude": lon,
        "altitude_km": alt,
        "velocity_kmh": speed,
        "o2_percent": o2,
        "cabin_pressure_kpa": pressure,
        "co2_percent": co2,
        "ambient_temp_c": temp,
        "air_flow_velocity_ms": flow,
        "smoke_obscuration_pct": smoke_destiny,
        "risk_score": risk
    }
    agent3_rows.append(row)

# Save Agent 3 CSV & JSON
a3_csv = os.path.join(DATASET_DIR, "agent3_iss_eclss_telemetry.csv")
with open(a3_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(agent3_rows[0].keys()))
    writer.writeheader()
    writer.writerows(agent3_rows)

a3_json = os.path.join(DATASET_DIR, "agent3_iss_eclss_telemetry.json")
with open(a3_json, "w", encoding="utf-8") as f:
    json.dump(agent3_rows, f, indent=2, ensure_ascii=False)

print(f"  -> Agent 3: Saved {len(agent3_rows)} telemetry records to CSV and JSON.")


# ==============================================================================
# 4. AGENT 4: NASA Flame Dynamics & Microgravity CFD Experimental Dataset (150 rows)
# Materials: PMMA, Polyethylene, Nomex, Heptane, Methane, Cotton, Kevlar
# Gravity levels: 0g (microgravity spherical) vs 1g (buoyant teardrop)
# ==============================================================================
print("Generating Agent 4 Data...")
materials = [
    {"key": "PMMA", "temp_base": 1950, "soot_base": 0.45, "loi": 16.5},
    {"key": "Polyethylene", "temp_base": 2050, "soot_base": 0.75, "loi": 17.0},
    {"key": "Nomex", "temp_base": 1650, "soot_base": 0.20, "loi": 28.5},
    {"key": "Heptane", "temp_base": 2150, "soot_base": 0.50, "loi": 13.5},
    {"key": "Methane", "temp_base": 2220, "soot_base": 0.15, "loi": 12.0},
    {"key": "Cotton", "temp_base": 1780, "soot_base": 0.35, "loi": 18.0}
]

agent4_rows = []
for i in range(150):
    mat = random.choice(materials)
    # 50% microgravity (0g), 50% earth gravity (1g) or partial
    g_choice = random.choice([0.0, 0.0, 0.0, 1.0, 1.0, 0.38, 0.16])
    o2 = round(random.uniform(14.0, 42.0), 1)
    pressure = round(random.uniform(40.0, 140.0), 1)
    flow_cms = round(random.uniform(0.5, 35.0), 1)

    is_quenched = (o2 < mat["loi"]) or (pressure < 25.0)

    if is_quenched:
        aspect = 0.0
        radius_mm = 0.0
        peak_temp_k = 298.0
        blue_ratio = 0.0
        flicker_hz = 0.0
        burn_rate = 0.0
        flame_shape = "EXTINGUISHED"
    else:
        # Microgravity physics: aspect ratio is ~1.0 (spherical); 1g stretches upward
        flow_stretch = 1.0 + (flow_cms / 30.0) * 0.35
        buoyancy_aspect = 1.0 + (g_choice * 2.4 * math.sqrt(pressure / 101.3))
        aspect = round(buoyancy_aspect * flow_stretch, 2)

        diffusion_broadening = 1.0 + (1.0 - g_choice) * 0.65
        radius_mm = round(12.0 * diffusion_broadening * (o2 / 21.0)**0.4 * (101.3 / pressure)**0.25, 1)
        peak_temp_k = round(mat["temp_base"] + (o2 - 21.0) * 28.0 - (1.0 - g_choice) * 140.0, 1)

        soot_idx = round(min(1.0, mat["soot_base"] * (pressure / 101.3)**0.8 * (0.6 + 0.4 * g_choice)), 2)
        blue_ratio = round(max(0.05, min(0.95, (1.0 - g_choice) * 0.75 + (0.2 if o2 > 24 else 0.05) - soot_idx * 0.3)), 2)
        flicker_hz = round(g_choice * (12.5 * math.sqrt(g_choice) + (pressure / 100.0) * 1.5), 1)
        burn_rate = round(0.09 * (o2 / 21.0)**1.2 * math.sqrt(pressure / 101.3) * (0.7 + 0.3 * g_choice), 3)
        flame_shape = "SPHERICAL_DIFFUSION" if g_choice < 0.2 else "BUOYANT_TEARDROP"

    row = {
        "id": i + 1,
        "fuel_material": mat["key"],
        "gravity_level_g": g_choice,
        "sim_o2_percent": o2,
        "sim_pressure_kpa": pressure,
        "sim_flow_velocity_cms": flow_cms,
        "flame_shape": flame_shape,
        "aspect_ratio": aspect,
        "flame_radius_mm": radius_mm,
        "peak_temperature_k": peak_temp_k,
        "blue_chemiluminescence_ratio": blue_ratio,
        "flicker_frequency_hz": flicker_hz,
        "burning_rate_mms": burn_rate
    }
    agent4_rows.append(row)

# Save Agent 4 CSV & JSON
a4_csv = os.path.join(DATASET_DIR, "agent4_flame_cfd_experiments.csv")
with open(a4_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(agent4_rows[0].keys()))
    writer.writeheader()
    writer.writerows(agent4_rows)

a4_json = os.path.join(DATASET_DIR, "agent4_flame_cfd_experiments.json")
with open(a4_json, "w", encoding="utf-8") as f:
    json.dump(agent4_rows, f, indent=2, ensure_ascii=False)

print(f"  -> Agent 4: Saved {len(agent4_rows)} combustion CFD experiments to CSV and JSON.")

# ==============================================================================
# 5. Scientific Array Format Sample for Agent 4 & 1
# ==============================================================================
a4_matrix = os.path.join(DATASET_DIR, "agent4_cfd_scientific_matrix.txt")
with open(a4_matrix, "w", encoding="utf-8") as f:
    f.write("# NASA CIR Droplet Combustion Scientific Matrix [Gravity_g, O2_%, Pressure_kPa, Flow_cms, Aspect_Ratio, Flame_Radius_mm, Temp_K]\n")
    for r in agent4_rows[:40]:
        f.write(f"{r['gravity_level_g']}\t{r['sim_o2_percent']}\t{r['sim_pressure_kpa']}\t{r['sim_flow_velocity_cms']}\t{r['aspect_ratio']}\t{r['flame_radius_mm']}\t{r['peak_temperature_k']}\n")

print("  -> Scientific Matrix file saved: agent4_cfd_scientific_matrix.txt")
print("\nALL DATASETS GENERATED SUCCESSFULLY IN sample_datasets/!")
