<div align="center">

<img src="docs/logo.svg" width="140" alt="SPC"/>

# SPC — SAZ Proxy Collector

### **v0.6.0** — «نسخهٔ بالغ» 🌷

**۵۰ کانفیگ و ۳۰ پروکسی برتر ۲۴ ساعت — از محبوب‌ترین کانال‌های تلگرام ایران**

[![GitHub](https://img.shields.io/badge/GitHub-THE--SAZ-181717?style=for-the-badge&logo=github)](https://github.com/THE-SAZ)
[![Telegram](https://img.shields.io/badge/Telegram-THE__SAZ-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/THE_SAZ)
[![Live](https://img.shields.io/badge/🌐-Live-ff4d6d?style=for-the-badge)](https://the-saz.github.io/SPC/)
[![Version](https://img.shields.io/badge/v-0.6.0-7c3aed?style=for-the-badge)](#)
[![Update](https://img.shields.io/badge/⏱-Every_12h-22d3ee?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[🌐 داشبورد](https://the-saz.github.io/SPC/) · [📦 مخزن](https://github.com/THE-SAZ/SPC) · [👤 توسعه‌دهنده](https://github.com/THE-SAZ)

</div>

---

## 🆕 چه چیزی در v0.6.0؟

### 🐛 رفع ۱۵ باگ مهم
- **Race condition در workflow** — ادغام job‌ها و ترتیب صحیح
- **دسترسی نداشتن به داده‌ها در Pages** — مسیر `docs/data`
- **QRCode race** — retry + fallback
- **favKey غیرپایدار** — SHA-1 hash
- **Pyrogram با credentials خالی** — گارد + پیام واضح
- و ۱۰ باگ دیگر در جدول [`CHANGELOG`](#-changelog)

### ✨ ویژگی‌های جدید
- 🎨 **لوگوی سه‌بعدی جدید** — با radialGradient، shadow و highlight دقیق
- 💎 **داشبورد بالغ** — Design Tokens، typography scale، micro-interactions
- ⚡ **تأخیر پاسخ سریع‌تر** — `?t=` cache-buster + Service Worker هوشمند
- 🔥 **رتبه‌بندی سه‌پله** — طلایی/نقره‌ای/برنزی
- ⏱ **شمارش معکوس ثانیه‌ای** تا آپدیت بعدی
- 🌍 **پرچم + کد کشور** برای هر سرور
- 💾 **کش تاریخچه ۳۰ روزه** — امتیاز پایداری
- 📊 **آمار پیشرفته** — میانگین + سریع‌ترین
- 🎯 **PWA کامل** — نصب روی iOS/Android
- ♿ **A11y بهتر** — `aria-label`, `role`, keyboard support

---

## 🚀 نصب و راه‌اندازی

```bash
git clone https://github.com/THE-SAZ/SPC.git
cd SPC
pip install -r requirements.txt
python src/main.py
```

### 🔐 Secrets (۳ مورد)

| نام | منبع |
|-----|------|
| `TELEGRAM_API_ID` | [my.telegram.org](https://my.telegram.org) |
| `TELEGRAM_API_HASH` | [my.telegram.org](https://my.telegram.org) |
| `TELEGRAM_SESSION` | رشتهٔ Pyrogram |

**تنظیم:**
1. `Settings → Secrets and variables → Actions` → افزودن ۳ سکرت
2. `Settings → Pages` → Source: **GitHub Actions**
3. تب Actions → Run workflow

---

## 🔗 استفاده

### 📱 QR اسکن (ساده‌ترین راه)

روی هر کانفیگ در داشبورد دکمهٔ **📱** را بزن → در v2rayNG / Streisand / Shadowrocket اسکن کن.

### 🔗 لینک اشتراک (خودکار)

```
https://the-saz.github.io/SPC/sub64.txt
```

را در اپ خود وارد کن → همهٔ کانفیگ‌ها **هر ۱۲ ساعت خودکار** آپدیت می‌شوند.

---

## 🏗 معماری

```
GitHub Actions (cron: 12h)
      │
      ▼
┌─────────────────────────────────┐
│  Python Core v0.6.0              │
│  ├─ Telegram Scraper (Pyrogram)  │
│  ├─ Config/Proxy Parser (Regex)  │
│  ├─ TCP Validator (80 conc.)     │
│  ├─ GeoIP (ip-api batch)         │
│  ├─ History (30-day cache)       │
│  └─ Prices + Date (multi-fallback)│
└──────────────┬──────────────────┘
               ▼
        docs/data/*.json  →  GitHub Pages
               │
               ▼
     Dashboard (PWA + iOS-Optimized)
```

---

## 📁 ساختار

```
SPC/
├── .github/workflows/update.yml
├── src/main.py
├── docs/
│   ├── index.html
│   ├── logo.svg
│   ├── manifest.json
│   ├── sw.js
│   ├── sub.txt / sub64.txt
│   └── data/
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📋 Changelog

<details>
<summary><strong>v0.6.0 — «نسخهٔ بالغ»</strong></summary>

**رفع باگ (۱۵ مورد):**
1. Race condition در workflow → job واحد
2. داده‌ها در Pages در دسترس نبودند → `docs/data`
3. `data` path در هر دو شرط fetch → حذف شرط
4. Service Worker subpath → `./sw.js` + scope
5. QRCode race → retry + placeholder
6. `favKey` غیرپایدار → SHA-1
7. `_vmess_host_port` با fragment → strip
8. Pyrogram با API_ID=0 → گارد
9. countdown بدون `next` → fallback
10. `prices_cache` → partial save
11. Regex با backtick → بهبود
12. `Cache-Control` → `?t=` timestamp
13. `msg.caption` → پشتیبانی
14. Semaphore منفی → clamp
15. جستجو با پورت → type check

**قابلیت‌ها:**
- Design Tokens + Typography Scale
- لوگوی سه‌بعدی SVG
- رتبه‌بندی طلایی/نقره‌ای/برنزی
- شمارش معکوس ثانیه‌ای
- GeoIP + پرچم
- تاریخچه ۳۰ روزه
- PWA کامل + A11y

</details>

<details>
<summary>v0.0.5</summary>

- QR Code, Subscription, GeoIP, Stability, Favorites, Themes, Stats, Filters

</details>

---

## 🛠 فناوری

`Python 3.12` · `Pyrogram` · `aiohttp` · `jdatetime` · `ip-api` · `PriceDB` · `Vazirmatn` · `Glassmorphism` · `PWA` · `GitHub Actions`

---

## 📄 لایسنس

MIT © 2026 [THE SAZ](https://github.com/THE-SAZ)

<div align="center">

**ساخته‌شده با ❤️ توسط THE SAZ**

[GitHub](https://github.com/THE-SAZ) · [Telegram](https://t.me/THE_SAZ)

</div>
