# ⚡ NexusLock (Multi-Game Server Selector & Firewall Locker)

<div align="center">

أداة متطورة وخفيفة لنظام ويندوز لعزل وحظر سيرفرات الألعاب وتثبيت الاتصال بالسيرفر الأفضل مباشرة عبر جدار حماية ويندوز (**Windows Firewall**)، بدون VPN وبدون برامج وسيطة ترفع البنق.

<br>

[![Latest Release](https://img.shields.io/github/v/release/omar-hisham26/NexusLock?color=10b981&label=الإصدار_الحالي&style=for-the-badge&logo=github)](https://github.com/omar-hisham26/NexusLock/releases/latest)
[![Platform](https://img.shields.io/badge/نظام_التشغيل-Windows_10_/_11-38bdf8?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/omar-hisham26/NexusLock/releases/latest)
[![License](https://img.shields.io/badge/الترخيص-MIT-f59e0b?style=for-the-badge)](LICENSE)

<br><br>

### ⬇️ روابط التحميل المباشرة (Direct Download Links)

&nbsp;&nbsp;
[![تحميل مثبت الويندوز](https://img.shields.io/badge/📦_تحميل_مثبت_الويندوز_(Setup)-NexusLock--Setup.exe-38bdf8?style=for-the-badge&logo=inno-setup&logoColor=white)](https://github.com/omar-hisham26/NexusLock/releases/latest/download/NexusLock-Setup.exe)

<br>

*التحميل يبدأ مباشرة من أحدث إصدار (Latest Release) على GitHub.*

</div>

---

## 🚀 شاشة البداية ومحدث ديسكورد التلقائي (Discord-Style Auto-Updater)
* **نافذة فخمة في منتصف الشاشة بدون حواف أو أزرار ويندوز التقليدية** (Frameless Splash Screen) متناسقة مع ثيم التطبيق الداكن وشعار البرنامج.
* **تحديثات تلقائية سريعة عبر GitHub Releases:**
  - عند تشغيل البرنامج، يتحقق فوراً من توفر أي إصدار أحدث.
  - في حال توفر تحديث، يقوم بتحميله تلقائياً مع شريط تقدم حي للنسبة المئوية، ثم يستبدل الملف ويعيد التشغيل بالنسخة الجديدة فوراً.
  - في حال كان البرنامج محدثاً، ينتقل مباشرة إلى الواجهة الرئيسية بسلاسة فائقة.

---

## 🎮 الألعاب التي تدعمها الأداة (Supported Games)

| اللعبة | المنصة | الخوادم المتاحة | طريقة الحظر | حالة الدعم |
| :--- | :--- | :--- | :--- | :--- |
| **Overwatch 2** | Blizzard Battle.net / Steam | 11 منطقة عالمية (نيذرلاند، السعودية، فنلندا، أمريكا، سنغافورة، اليابان...) | حظر السيرفرات الفرعية عبر Windows Firewall | 🟢 مدعوم بالكامل 100% |
| **Deadlock** | Valve Steam | 33 منطقة وسيرفر (نيذرلاند، فرانكفورت، دبي، لندن، باريس، مدريد، فيينا...) | حظر ريلايات Valve SDR الرسمية | 🟢 مدعوم بالكامل 100% |
| **Counter-Strike 2 (CS2)** | Valve Steam | شبكة Valve SDR | حظر الخوادم البعيدة | 🟡 قيد التجهيز |
| **Marvel Rivals** | NetEase Games | مراكز بيانات NetEase | حظر السيرفرات الخارجية | 🔵 قريباً |
| **Apex Legends** | EA App / Steam | خوادم Respawn | عزل مناطق الاتصال | 🔵 قريباً |

---

## 🛡️ مميزات الأمان وضمان عدم الباند (Zero-Ban Guarantee)
* البرنامج **لا يعدل ملفات اللعبة** نهائياً ولا يحقن أي كود في الذاكرة (No DLL / Memory Injection).
* جميع عمليات التحكم تتم عبر جدار الحماية القياسي لنظام ويندوز (**Windows Firewall**).
* آمن للاستخدام 100% في المباريات التنافسية (Competitive / Ranked).

---

## 📁 هيكلة المشروع (Project Architecture)
```
NexusLock/
├── assets/                       # شعارات وأيقونات الألعاب والشعار الرئيسي
│   ├── app_icon.png
│   ├── deadlock.png              # شعار لعبة Deadlock
│   ├── overwatch.png             # شعار لعبة Overwatch 2
│   └── icon.ico
├── data/                         # بيانات ونطاقات السيرفرات
│   ├── deadlock_servers.json     # سيرفرات Valve SDR الرسمية لـ Deadlock
│   └── overwatch_servers.json    # سيرفرات ونطاقات Blizzard لـ Overwatch 2
├── src/                          # الكود المصدري المنظم
│   ├── config.py                 # الإعدادات ورابط GitHub ومسارات الحفظ
│   ├── core/                     # النواة والتعامل مع النظام
│   │   ├── admin.py              # فحص وطلب صلاحيات المسؤول (UAC)
│   │   ├── firewall.py           # إدارة جدار حماية ويندوز بصمت وسرعة
│   │   ├── network.py            # فحص البنق الحي وتنظيف كاش الـ DNS
│   │   └── updater.py            # محرك التحقق وتنزيل التحديثات السحابية
│   ├── games/                    # بروفايلات الألعاب المدعومة
│   │   ├── base.py               # كلاس اللعبة الأساسي المشترك
│   │   ├── overwatch.py          # معالج Overwatch 2 وخوادمه الـ 11
│   │   └── deadlock.py           # معالج Deadlock وخوادمه الـ 33
│   └── ui/                       # واجهة المستخدم (Modern UI)
│       ├── theme.py              # الألوان والخطوط ودعم DPI
│       ├── components.py         # الأزرار والبطاقات المخصصة
│       ├── splash.py             # شاشة البداية بدون إطار بنمط Discord
│       ├── sidebar.py            # الشريط الجانبي الأيسر للتنقل
│       ├── catalog_view.py       # شاشة عرض الألعاب المدعومة والقادمة
│       ├── game_view.py          # لوحة التحكم واختيار السيرفر لكل لعبة
│       └── app.py                # النافذة الرئيسية والتنسيق العام
├── main.py                       # نقطة التشغيل الرئيسية
├── build.bat                     # سكربت التجميع وبناء الـ exe
└── installer.iss                 # سكربت توليد برنامج التثبيت
```

---

<div align="center">

### 📥 [اضغط هنا للدخول لصفحة Releases على GitHub](https://github.com/omar-hisham26/NexusLock/releases/latest)

</div>
