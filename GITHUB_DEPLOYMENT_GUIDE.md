# دليل نقل ورفع المشروع إلى GitHub وربطه بالفرونت إند
## Moving from Localhost to GitHub & Cloud Deployment

تمت تهيئة المشروع بالكامل ليصبح جاهزاً للنقل والرفع المباشر إلى **GitHub** والعمل على رابط سحابي حي (Cloud URL) بدلاً من الـ Localhost، مع مراعاة كافة خانات الربط ثنائية الاتجاه بالفرونت إند.

---

### 📂 1. الملفات الجديدة المجهزة للـ GitHub والنشر السحابي

1. **[`api_client.js`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/api_client.js):** 
   - ملف SDK جافاسكريبت متكامل تنقله مباشرة لمشروع الفرونت إند بتاعك.
   - يربط كافة الوكلاء الأربعة بسطر إعداد واحد فقط.
2. **[`.gitignore`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/.gitignore):**
   - يتجاهل قواعد البيانات المحلية المؤقتة وملفات الكاش التلقائية ليبقى الريبو نظيفاً.
3. **[`Dockerfile`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/Dockerfile):**
   - حاوية دوكر سريعة وخفيفة لأي منصة استضافة سحابية.
4. **[`render.yaml`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/render.yaml):**
   - لنشر السيرفر مجاناً بضغطة زر واحدة على Render.com.
5. **[`requirements.txt`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/requirements.txt):**
   - يوضح أن المشروع صفر-مكتبات خارجية (Zero-dependency) ويعمل على أي بيئة بايثون 3.9+.

---

### 🚀 2. خطوات رفع المشروع على حسابك في GitHub (اختر الطريقة الأسهل لك)

#### الطريقة الأولى (الأسهل والأسرع - عبر موقع GitHub مباشرة):
1. افتح حسابك على [GitHub.com/new](https://github.com/new) وأنشئ مستودعاً جديداً (New Repository) وسمّه مثلاً: `nasa-space-fire-ai`.
2. بعد إنشاء المستودع، اضغط على خيار **"uploading an existing file"**.
3. اسحب وأفلت (Drag and Drop) جميع ملفات ومجلدات المشروع من المسار:
   `C:\Users\ASUS\.gemini\antigravity\scratch\nasa_space_fire_ai`
4. اضغط **"Commit changes"**.

#### الطريقة الثانية (عبر برنامج GitHub Desktop):
1. افتح تطبيق GitHub Desktop واختر **File -> Add Local Repository**.
2. اختر المجلد: `C:\Users\ASUS\.gemini\antigravity\scratch\nasa_space_fire_ai`.
3. اضغط **Publish repository to GitHub**.

#### الطريقة الثالثة (عبر سطر الأوامر Git CLI):
```bash
cd "C:\Users\ASUS\.gemini\antigravity\scratch\nasa_space_fire_ai"
git init
git add .
git commit -m "NASA Space Fire AI Brain v3.1 Cloud-Ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nasa-space-fire-ai.git
git push -u origin main
```

---

### 🌐 3. كيف تجعل السيرفر يعمل على رابط إنترنت سحابي مجاناً في دقيقة (Free Cloud Hosting)

بمجرد رفع المشروع على GitHub، يمكنك تشغيله على رابط إنترنت دائم يعمل 24/7 دون الحاجة لتشغيل جهازك:

1. افتح موقع **[Render.com](https://render.com)** (أو **Railway.app**).
2. سجل دخول بحساب GitHub واختر **"New Web Service"**.
3. اختر المستودع `nasa-space-fire-ai` الذي رفعته للتو.
4. اترك الإعدادات كما هي واضغط **"Create Web Service"**.
5. سيعطيك Render رابطاً حياً ودائماً مثل:
   👉 `https://nasa-space-fire-ai.onrender.com`

---

### 🔗 4. ربط برنامج الفرونت إند بتاعك بالرابط الجديد (أسهل مما تتخيل!)

في مشروع الفرونت إند الذي ستطوره، انسخ الملف [`api_client.js`](file:///C:/Users/ASUS/.gemini/antigravity/scratch/nasa_space_fire_ai/api_client.js) بجانب ملفات مشروعك، واستخدمه كالتالي:

```javascript
// 1. استيراد العميل وتوجيهه للرابط السحابي على GitHub/Render
import SpaceFireClient from './api_client.js';

// ضع رابط السيرفر المرفوع (أو localhost أثناء التطوير)
const client = new SpaceFireClient('https://nasa-space-fire-ai.onrender.com');

// -------------------------------------------------------------
// العميل 1: إرسال المتغيرات واستقبال نسبة الخطر والتشخيص
// -------------------------------------------------------------
const riskResult = await client.predictFireRisk({
  o2_percent: 24.5,
  cabin_pressure_kpa: 101.3,
  ambient_temp_c: 28.0,
  co_percent: 0.2 // أي خانة أضفتها للسيستم!
});

// ربط المخرجات بعناصر واجهتك:
document.getElementById('risk_val').innerText = `${riskResult.fire_probability_percent}%`;
document.getElementById('hazard_badge').innerText = riskResult.hazard_level;
document.getElementById('ai_text').innerText = riskResult.description;

// -------------------------------------------------------------
// العميل 2: شات بوت طوارئ الفضاء (Grounded RAG)
// -------------------------------------------------------------
const chatResult = await client.askSafetyAssistant('دخان ورائحة شياط في لوحة القواطع');
console.log('تشخيص العطل:', chatResult.root_cause_diagnosis);
console.log('خطوات السلامة:', chatResult.recommended_actions);

// -------------------------------------------------------------
// العميل 3: استقبال بث محطة الفضاء ISS لايف كل ثانية
// -------------------------------------------------------------
const issStream = client.subscribeISSTelemetry((livePacket) => {
  // يتحدث كل ثانية بدون تدخل المستخدم
  console.log('بيانات الحساسات:', livePacket.atmospheric_telemetry);
  console.log('تقييم الخطر اللحظي:', livePacket.ai_fire_hazard_evaluation);
});

// -------------------------------------------------------------
// العميل 4: محاكاة اللهب البصري ورسمه في الكانفاس
// -------------------------------------------------------------
const flameSim = await client.simulateFlame({
  fuel_material: 'PMMA',
  gravity_level_g: 0.0, // انعدام جاذبية
  sim_o2_percent: 21.0
});

// رسم مسار اللهب في الـ SVG بواجهتك:
document.getElementById('flame_svg').setAttribute('d', flameSim.visual_spec.svg_outer_path);
```

---

### 🌟 أهم التغييرات التي تمت لنقل المشروع من الـ Self-Host:
1. **انعدام الاعتماد على `localhost:8500`:** أصبح السيرفر يكتشف رابطه العام تلقائياً من الـ Request Headers، ويولد لك أكواد الـ API المحدثة بالدومين الحقيقي.
2. **عقد الـ 2-Way جاهز في ملف واحد (`api_client.js`):** لم تعد بحاجة لكتابة طلبات `fetch` يدوية أو إدارة اتصالات الـ SSE المعقدة في الفرونت؛ فكل خانة أصبحت دالة برمجية صريحة.
3. **جاهزية النشر السحابي:** لن تحتاج لتثبيت أي مكتبات أو سيرفرات معقدة؛ المشروع يعمل تلقائياً بمجرد رفعه.
