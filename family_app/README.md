# قائمتنا

تطبيق ويب بسيط لك ولملاك: قائمة نواقص مشتركة، قائمة أمنيات، واقتراحات أكل.

## التشغيل محليًا (للتجربة على جهازك)

```bash
pip install -r requirements.txt
python app.py
```

يفتح على `http://localhost:5000` ويستخدم قاعدة بيانات SQLite محلية (ملف `app.db`) تلقائيًا لو ما فيه `DATABASE_URL`.

كلمة السر الافتراضية محليًا: `1234` (غيّرها من `.env` أو من متغير `APP_PASSCODE`).

## النشر أونلاين (خطوة بخطوة)

### 1. قاعدة البيانات - Supabase
1. سوي حساب على [supabase.com](https://supabase.com) وأنشئ مشروع جديد.
2. من إعدادات المشروع: **Project Settings -> Database -> Connection string -> URI**.
3. انسخ الرابط (يبدأ بـ `postgresql://postgres:...`).

### 2. رفع الكود - GitHub
1. سوي مستودع جديد على GitHub وارفع فيه هذا المجلد كامل.

### 3. الاستضافة - Render
1. سوي حساب على [render.com](https://render.com) واربطه بحساب GitHub.
2. اختر **New -> Web Service** واختر المستودع.
3. Render بيقرأ ملف `render.yaml` تلقائيًا ويقترح عليك الإعدادات.
4. عبّي متغيرات البيئة دي من لوحة تحكم Render:
   - `APP_PASSCODE`: كلمة السر اللي تبوها
   - `DATABASE_URL`: الرابط اللي نسخته من Supabase
   - `GEMINI_API_KEY`: (اختياري) مفتاح من [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
5. اضغط **Create Web Service**. أول نشر ياخذ شوية دقايق.

بعدها بتاخذ رابط زي `https://qaimatna.onrender.com` — هذا الرابط تفتحوه أنت وملاك وتضيفوه كأيقونة على الشاشة الرئيسية من المتصفح.

### ملاحظة عن الخطة المجانية
لو التطبيق ما تفتحش لأكثر من 15 دقيقة، Render يوقف السيرفر مؤقتًا، وأول فتح بعدها ياخذ حوالي 30-50 ثانية يصحى. طبيعي وما فيه حل غير الترقية لخطة مدفوعة.

## هيكل المشروع

```
app.py          - المسارات الرئيسية (routes)
models.py       - جداول قاعدة البيانات
config.py       - الإعدادات ومتغيرات البيئة
templates/      - صفحات HTML
static/         - CSS + ملف الـ PWA
```
