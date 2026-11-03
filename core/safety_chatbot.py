"""
Agent 2: Spacecraft Fire Incident Safety & Root-Cause AI Assistant.
Analyzes user-described fire anomalies, pinpoints technical root causes,
and provides step-by-step NASA emergency response & containment protocols.
"""

import re
from typing import Dict, Any, List

# NASA Spacecraft Fire Emergency Knowledge Base
INCIDENT_PATTERNS = [
    {
        "keywords": ["كهرباء", "شرر", "سلك", "قاطع", "لوحة", "فيش", "arc", "wire", "electrical", "breaker", "spark"],
        "category": "ELECTRICAL_ARCING_BREAKDOWN",
        "root_cause_ar": "قوس تفريغ كهربائي (Electrical Arcing) وتلف في العزل البوليمري لكابلات توزيع الطاقة أو تراكم حمل زائد على قاطع الدائرة.",
        "root_cause_en": "Electrical arc tracking and polymer insulation thermal breakdown due to localized overcurrent.",
        "affected_subsystem": "نظام توزيع الطاقة الكهربائية (EPS / Avionics Rack)",
        "hazard_level": "مرتفع (HIGH RISK)",
        "immediate_actions": [
            "ارتداء قناع التنفس الطارئ (PBA / PBE Mask) فوراً لحماية الجهاز التنفسي من غازات تحلل عوازل الأسلاك السامة (HF, CO).",
            "فصل التيار الكهربائي عن الحجرة المتضررة (Depower Rack) من خلال فتح القواطع المعنية أو إرسال أمر عبر قمرة التحكم.",
            "إغلاق صمامات التهوية القسرية للمقصورة فوراً لمنع انتشار الدخان عبر مجاري التكييف ومحاصرة أي هواء مؤكسد.",
            "تجهيز طفاية الرذاذ المائي الدقيق المعزول (Fine Water Mist Extinguisher) أو طفاية ثاني أكسيد الكربون المخصصة للإلكترونيات.",
            "استخدام مقياس الحرارة بالأشعة تحت الحمراء (Thermal Imager) لتحديد النقطة الساخنة خلف اللوحة المغلقة قبل الفتح."
        ]
    },
    {
        "keywords": ["بطارية", "ليثيوم", "حرارة متصاعدة", "انتفاخ", "فرقعة", "battery", "lithium", "runaway", "thermal"],
        "category": "BATTERY_THERMAL_RUNAWAY",
        "root_cause_ar": "انفلات حراري في خلايا بطارية الليثيوم (Lithium-ion Thermal Runaway) ناتج عن قصر دائرة داخلي (Internal Short) أو خلل في دائرة شحن وتبريد الخلايا.",
        "root_cause_en": "Internal cell short circuit leading to progressive exothermic thermal runaway.",
        "affected_subsystem": "وحدات تخزين الطاقة المحمولة أو بطاريات الأنظمة الاحتياطية",
        "hazard_level": "حرج للغاية (CRITICAL EMERGENCY)",
        "immediate_actions": [
            "إعلان حالة طوارئ الحريق من الدرجة الأولى فوراً، والتزام جميع أفراد الطاقم بأقنعة التنفس المستقلة.",
            "تطبيق التبريد الإيجابي المستمر: غمر أو رش حقيبة احتواء البطارية باستخدام طفاية الرذاذ المائي المعتمدة لكسر السلسلة الحرارية المتولدة ذاتياً.",
            "نقل الوحدة بعد احتوائها إلى كيس احتواء البطاريات الحراري المقاوم للانفجار (Thermal Containment Bag).",
            "عزل الوحدة المتضررة في غرفة معادلة الضغط (Airlock) إذا تعذر كبح الانبعاثات الغازية الكثيفة.",
            "تشغيل نظام تنقية الغازات السامة (Trace Contaminant Control System - TCCS) بأقصى طاقة."
        ]
    },
    {
        "keywords": ["مروحة", "محرك", "تهوية", "احتكاك", "صوت", "صرير", "محمل", "fan", "motor", "bearing", "friction", "eclss"],
        "category": "MECHANICAL_BEARING_FRICTION",
        "root_cause_ar": "احتكاك ميكانيكي حاد في محامل مروحة التهوية (Bearing Seizure) وتراكم حراري موضعي نتيجة غياب الحمل الحراري الطبيعي في انعدام الجاذبية.",
        "root_cause_en": "Bearing mechanical friction and thermal build-up in cabin air circulation assembly.",
        "affected_subsystem": "نظام دعم الحياة والتحكم البيئي (ECLSS Ventilation)",
        "hazard_level": "متوسط إلى مرتفع (MODERATE TO HIGH)",
        "immediate_actions": [
            "إيقاف تشغيل وحدة المروحة المعنية فوراً عبر واجهة نظام ECLSS لمنع استمرار الاحتكاك المولد للحرارة.",
            "عزل مجرى الهواء المرتبط بالمروحة لمنع انتقال الغازات الساخنة أو السخام إلى باقي أقسام المحطة.",
            "فحص درجة حرارة غلاف المحرك باستخدام مسبار الحرارة بالأشعة تحت الحمراء للتأكد من نزولها تحت 60°C.",
            "التأكد من عدم وجود شوائب أو قطع أقمشة عالقة في شفرات المروحة تسببت في إعاقة الدوران.",
            "تبديل دورة التهوية إلى الخط الاحتياطي (Redundant Fan Loop) لضمان عدم ركود الهواء حول الرواد."
        ]
    },
    {
        "keywords": ["أكسجين", "تسريب", "صمام", "أنبوب", "توهج", "لهب أزرق", "oxygen", "leak", "valve", "o2", "flare"],
        "category": "OXYGEN_ENRICHED_COMBUSTION",
        "root_cause_ar": "تسريب موضعي لغاز الأكسجين عالي النقاوة بالقرب من مادة قابلة للاشتعال أو شحنة ساكنة، مما خفض طاقة التنشيط وأدى لاشتعال غني بالأكسجين.",
        "root_cause_en": "High-pressure oxygen leak creating hyperoxic ignition zone with catastrophic propagation rate.",
        "affected_subsystem": "خطوط إمداد الأكسجين (Oxygen Recharge & Delivery System)",
        "hazard_level": "حرج للغاية (EXTREME EMERGENCY)",
        "immediate_actions": [
            "إغلاق صمامات عزل الأكسجين اليدوية والآلية الرئيسية (O2 Supply Isolation Valves) على الفور لقطع المؤكسد عن منطقة التفاعل.",
            "حظر استخدام أي مفاتيح كهربائية أو أجهزة لاسلكية في محيط الحادث لتجنب حدوث شرارات كهربائية ثانوية.",
            "إخلاء الوحدة إلى وحدة مجاورة وإغلاق كوة الضغط (Hatch) لمنع انتقال الغازات وإمكانية تخفيض الضغط لمحاصرة الحريق إذا لزم الأمر.",
            "استخدام طفاية ثاني أكسيد الكربون (CO2) لتقليص تركيز الأكسجين المحيط بالبؤرة بسرعة.",
            "مراقبة حساسات نسبة الأكسجين حتى عودة التركيز إلى النطاق الآمن (أقل من 22%)."
        ]
    }
]

GENERAL_SPACE_FIRE_PROTOCOL = [
    "1. ارتداء أجهزة التنفس الطارئة (PBA) لحماية العينين والرئتين من الأدخنة الكيميائية السامة.",
    "2. إيقاف الطاقة الكهربائية (Depower) عن الوحدة أو الجهاز مصدر العطل لقطع مصدر الطاقة الحرارية.",
    "3. إيقاف مراوح التهوية المشتركة (Inter-module Air Flow) لمنع تزويد الحريق بالأكسجين وتفادي نشر الدخان.",
    "4. تفريغ الطفاية المعتمدة (رذاذ مائي دقيق أو CO2) باتجاه قاعدة النقطة الساخنة.",
    "5. قياس تركيزات الغازات السامة (CO, CO2, HCN, HF) والتأكد من انطفاء الحريق تماماً قبل إعادة تشغيل الأنظمة."
]


class SafetyChatbotEngine:
    """Agent 2 Incident Assistant."""

    def __init__(self):
        pass

    def analyze_incident(self, user_description: str) -> Dict[str, Any]:
        """
        Parses the user's description, detects probable root cause,
        and provides specific action checklists and advice.
        """
        desc_lower = user_description.lower()

        matched_incident = None
        max_matches = 0

        for inc in INCIDENT_PATTERNS:
            match_count = sum(1 for kw in inc["keywords"] if kw in desc_lower)
            if match_count > max_matches:
                max_matches = match_count
                matched_incident = inc

        if matched_incident and max_matches >= 1:
            root_cause = matched_incident["root_cause_ar"]
            subsystem = matched_incident["affected_subsystem"]
            hazard = matched_incident["hazard_level"]
            actions = matched_incident["immediate_actions"]
            category = matched_incident["category"]

            response_text = (
                f"🚨 **تشخيص الذكاء الاصطناعي لحالة الطوارئ ({hazard})**:\n\n"
                f"🔍 **سبب المشكلة / العطل الفني المرجح:**\n{root_cause}\n\n"
                f"⚙️ **النظام الفرعي المتأثر:** {subsystem}\n\n"
                f"🛡️ **إجراءات السلامة الفورية الواجب اتخاذها:**\n" +
                "\n".join([f"{i+1}. {act}" for i, act in enumerate(actions)]) +
                "\n\n💡 **ملاحظة بيئية فضائية:** نظراً لانعدام الجاذبية في المركبة، لا يصعد الدخان إلى الأعلى تلقائياً بل ينتشر في اتجاه تيارات مراوح التهوية، لذا فإن إيقاف التهوية وفصل الطاقة يمثلان خط الدفاع الحاسم الأول."
            )
        else:
            root_cause = "اشتعال موضعي أو انبعاث حراري ناتج عن خلل في أحد المكونات الداخلية أو احتكاك كهربائي/حراري غير محدد."
            subsystem = "مقصورة المركبة الفضائية العامة"
            hazard = "متوسط إلى مرتفع (تحت الفحص)"
            actions = GENERAL_SPACE_FIRE_PROTOCOL
            category = "GENERAL_SPACE_FIRE"

            response_text = (
                f"⚠️ **تشخيص الحادث الأولي:**\n\n"
                f"🔍 **سبب العطل المرجح:** {root_cause}\n\n"
                f"🛡️ **بروتوكول السلامة الطارئ المعتمد من ناسا (NASA Emergency Fire Response):**\n" +
                "\n".join([f"{act}" for act in actions]) +
                "\n\nيرجى تزويدي بمزيد من التفاصيل مثل: (هل توجد رائحة احتراق أسلاك؟ هل هناك توهج أو شرر؟ ما هو موقع الحادث بالتحديد؟) لدقة أكبر في تحديد سبب المشكلة."
            )

        return {
            "category": category,
            "root_cause_diagnosis": root_cause,
            "affected_subsystem": subsystem,
            "hazard_level": hazard,
            "recommended_actions": actions,
            "chat_response_markdown": response_text
        }
