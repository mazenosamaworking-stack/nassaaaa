# دليل البيانات التجريبية المولدة للوكلاء الأربعة
## NASA Space Fire AI Generated Datasets Guide

تم توليد وتجهيز حزم بيانات واقعية ومحاكية لمعايير ناسا الفضائية، موزعة في ملفات مستقلة لكل عميل (Agent) بصيغ متعددة (CSV و JSON و TXT):

---

### 🛰️ ملفات العميل 1: متنبئ خطر الحريق (Agent 1)
* **[`agent1_fire_risk_data.csv`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent1_fire_risk_data.csv)** (160 صفاً)
* **[`agent1_fire_risk_data.json`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent1_fire_risk_data.json)**
* **المحتوى:** بيانات احتراق للمركبات الفضائية تضم متغيرات غير متطابقة:
  * `o2_percent` (نسبة الأكسجين)
  * `cabin_pressure_kpa` (ضغط المقصورة)
  * `co2_percent` (ثاني أكسيد الكربون)
  * `ambient_temp_c` (حرارة المقصورة)
  * `air_flow_velocity_ms` (سرعة تيار التهوية)
  * `wire_temp_c` (حرارة عوازل الأسلاك)
  * `coolant_pressure_kpa` (ضغط سائل التبريد)
  * `risk_score` (نسبة الخطر المحسوبة كهدف للتدريب 0-100)

---

### 👨‍🚀 ملفات العميل 2: مساعد طوارئ وأعطال الحريق (Agent 2 - RAG Knowledge Base)
* **[`agent2_safety_emergency_manuals.txt`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent2_safety_emergency_manuals.txt)**
* **[`agent2_incident_reports.json`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent2_incident_reports.json)**
* **المحتوى:** أدلة وإجراءات طوارئ ناسا الرسمية المعتمدة لرواد الفضاء (NASA Flight Rules & Fire Emergency SOPs):
  1. تشخيص والتصدي لأقواس التفريغ الكهربائي (Electrical Arcing).
  2. بروتوكول مكافحة الانفلات الحراري لبطاريات الليثيوم (Lithium-Ion Runaway).
  3. أعطال احتكاك وتآكل محامل مراوح التهوية (ECLSS Fan Bearing Friction).
  4. بروتوكول تسريب خطوط الأكسجين النقي عالي الضغط.
  *(تُستخدم هذه الوثائق للبحث المباشر داخل الـ RAG ليجيب الموديل منها حصراً).*

---

### 🌍 ملفات العميل 3: راصد محطة الفضاء الدولية (Agent 3 - ISS Telemetry)
* **[`agent3_iss_eclss_telemetry.csv`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent3_iss_eclss_telemetry.csv)** (200 قراءة زمنية)
* **[`agent3_iss_eclss_telemetry.json`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent3_iss_eclss_telemetry.json)**
* **المحتوى:** سجلات تيليميتري حقيقية لحساسات وحدات Destiny و Columbus و Kibo في محطة ISS:
  * إحداثيات مدارية لحظية (`latitude`, `longitude`, `altitude_km`, `velocity_kmh`).
  * حساسات بيئية (`o2_percent`, `cabin_pressure_kpa`, `co2_percent`, `ambient_temp_c`, `air_flow_velocity_ms`).
  * حساسات كثافة الدخان (`smoke_obscuration_pct`).
  * نسبة الخطر المرجعية (`risk_score`).
  > **تنبيه:** رفع هذا الملف وتدريبه للعميل 3 يفتح فوراً شرط التدريب الإلزامي ويبدأ البث الحي في احتساب نسبة الخطر!

---

### 🔥 ملفات العميل 4: محاكي اللهب وبيانات CFD (Agent 4)
* **[`agent4_flame_cfd_experiments.csv`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent4_flame_cfd_experiments.csv)** (150 تجربة احتراق)
* **[`agent4_flame_cfd_experiments.json`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent4_flame_cfd_experiments.json)**
* **[`agent4_cfd_scientific_matrix.txt`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/sample_datasets/agent4_cfd_scientific_matrix.txt)** (مصفوفة علمية متصلة)
* **المحتوى:** تجارب احتراق وتخميد المواد في انعدام الجاذبية $0g$ والجاذبية الأرضية $1g$ (مستندة لتجارب NASA CIR و BASS):
  * المواد: PMMA, Polyethylene, Nomex, Heptane, Methane, Cotton.
  * القياسات: شكل اللهب، نسبة الاستطالة (Aspect Ratio)، نصف القطر بالملم، الحرارة القصوى بكلفن، نسبة الانبعاث الأزرق، وتردد الاهتزاز بالهرتز.

---

### 🚀 كيفية رفع وتدريب أي ملف في ثوانٍ:
1. افتح لوحة التحكم على: `http://localhost:8500`
2. اذهب لتبويب **"إدخال البيانات لكافة الوكلاء"**.
3. اختر العميل المستهدف (مثلاً: العميل 3 أو العميل 1).
4. اضغط على خيار **"رفع ملف من جهازك"** واختر الملف المطلوب من مجلد `sample_datasets`.
5. اضغط زر **"رفع البيانات وتدريب الـ AI للعميل"**.
