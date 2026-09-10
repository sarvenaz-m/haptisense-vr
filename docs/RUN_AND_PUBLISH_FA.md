# راهنمای اجرای نسخه پیشنهادی ۰٫۳ و انتقال به GitHub

این نسخه برای مخزن `sarvenaz-m/haptisense-vr` آماده شده است. در این تحویل هیچ
شاخه، commit، pull request یا انتشار جدیدی روی GitHub انجام نشده؛ اتصال افزونه
هنگام ساخت شاخه خطای 403 داده است. این موضوع به معنای رد شدن کد نیست.

## اول دمو را اجرا کن

پوشه `project` داخل بسته، سورس کامل است. ترمینال را داخل آن باز کن و اجرا کن:

```bash
python3 -m http.server 8000 --directory docs
```

در مرورگرت `http://localhost:8000/workbench.html` را باز کن. در ویندوز اگر
دستور `python3` شناخته نشد، از `python` استفاده کن.

- در صفحه Contact studio ابزار را با Play حرکت بده، زمان را جابه‌جا کن و
  دوربین را با کشیدن موس بچرخان.
- در Model comparison سه مدل را با حرکت یکسان مقایسه کن. هنگام نگه‌داشتن
  ابزار، حافظه ماده در مدل SLS کم می‌شود؛ عمق در این قسمت ثابت است.
- با Scan speed برابر صفر، دامنه ارتعاش باید صفر شود.
- JSON و CSV بگیر. JSON را دوباره وارد کن تا نرم‌افزار نتایج را از پارامترهای
  معتبر محاسبه کند؛ داده‌های واردشده را صرفاً نمایش نمی‌دهد.
- صفحه Perceptual protocol داده‌های مصنوعی قبلی را نشان می‌دهد؛ نتیجه آزمون
  انسانی جدید نیست.

## آزمون‌های عددی

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m haptisense research --output results/my-first-v03-run --model sls --protocol hold
```

در PowerShell به جای دستور `source` از `.venv\Scripts\Activate.ps1` استفاده کن.
برای آزمون‌های تطبیق مرورگر، Node.js و برای آزمون منطق firmware، g++ لازم است.
نبود این دو می‌تواند آزمون مربوط را SKIPPED کند؛ نتیجه واقعی را گزارش کن.
برای هر اجرای فرمان research یک پوشه خروجی تازه انتخاب کن.

## انتقال با Git، بدون بازنویسی تاریخچه

فایل `haptisense-v0.3-upgrade.patch` تغییرات را نسبت به این commit نگه می‌دارد:

`13d65e03220be16da0c27b022c58749cc82272d4`

از یک clone تازه استفاده کن تا کارهای ذخیره‌نشده قبلی‌ات آسیب نبیند:

```bash
git clone https://github.com/sarvenaz-m/haptisense-vr.git haptisense-vr-v03
cd haptisense-vr-v03
git rev-parse HEAD
```

اگر مقدار HEAD با شناسه بالا متفاوت بود، patch را بی‌بررسی اعمال نکن؛ تغییرات
جدید مخزن باید ابتدا تطبیق داده شوند. سپس فایل patch را در پوشه والد این clone
بگذار و این دستورات را اجرا کن:

```bash
git switch -c upgrade/research-workbench-v0.3
git apply --check ../haptisense-v0.3-upgrade.patch
git apply ../haptisense-v0.3-upgrade.patch
python -m pip install -e .
python -m unittest discover -s tests -v
git diff --check
git status --short
git add .
git diff --cached --stat
git commit -m "Add computational contact studio and reproducible research models"
git push -u origin upgrade/research-workbench-v0.3
```

پیش از commit، فایل‌های نمایش‌داده‌شده در status را بررسی کن؛ فایل خصوصی، کلید،
مدرک تحصیلی یا ویدئوی شخصی را اضافه نکن. این بسته فقط سورس و داده مصنوعی دارد.
ورود به GitHub را در محیط خودت انجام بده؛ رمز یا توکن را در چت نفرست.

پس از push در GitHub یک pull request از این شاخه به `main` باز کن. متن آماده
در `PR_DESCRIPTION.md` داخل بسته قرار دارد. ابتدا نتیجه workflow با نام `tests`
را بررسی کن. آزمون مرورگر خروجی `browser-validation` می‌سازد که شامل گزارش و
اسکرین‌شات‌های دسکتاپ و اندازه‌های ۳۹۰، ۷۶۸ و ۱۰۲۴ پیکسل است. این آزمون‌ها در
این تحویل هنوز اجرا نشده‌اند. فقط پس از بررسی نتیجه و ظاهر، merge کن.

GitHub Pages فعلی با تغییرات `docs/` در شاخه `main` به‌روز می‌شود. بعد از merge
و موفقیت deployment، مسیر `workbench.html` نسخه جدید را نمایش می‌دهد. پیش از
آن، لینک عمومی موجود همچنان نسخه قبلی است.

## برای ارائه به داور

می‌توانی «مدل‌سازی تماس، بررسی افت نیروی وابسته به زمان، مقایسه کنترل‌شده و
پیاده‌سازی قابل بازتولید» را همراه کد و نتایج ارائه کنی. ساخت دستگاه، اجرای
PHANTOM، آزمون انسانی، اجرای تأییدشده Unity یا نمره تضمینی از این کار حاصل نشده.
سورس با کمک AI تهیه شده است؛ قبل از ارائه باید بتوانی معادلات و کد را خودت
توضیح بدهی. برای ضبط دمو، فقط اجرای واقعی نرم‌افزار روی کامپیوترت را نشان بده.
