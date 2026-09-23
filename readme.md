# AI Architectural Copilot Telegram Bot

Arxitektura, muhandislik va loyihalash sohasidagi mutaxassislar (Arxitektor, Konstruktor, Smetachi, Dizayner) uchun har kungi vazifalar bo'yicha texnik ma'lumotnomalar (Dossier / Shpargalka) tayyorlab beruvchi AI yordamchi Telegram boti.

---

## 1. Asosiy Imkoniyatlar (Key Features)

- **19:00 Kechki Rejalashtirish**: Har kuni kechqurun soat 19:00da mutaxassisga bildirishnoma yuboriladi va ertangi kun topshirig'i (bino turi, qavatliligi, maxsus talablar) qabul qilinadi.
- **AI Tungi Tadqiqot**: Google Gemini 3.6 Flash yordamida loyiha uchun:
  - O'zbekiston milliy me'yorlari (**SHNK / QMQ**) va Toshkent shahri Dizayn Kodi.
  - Mahalliy iqlimga mos arzon va sifatli materiallar hamda ularni xarid qilish manzillari (*O'rikzor, Bekto'pi, Arton Gazoblok zavodi, Akfa*).
  - Yashil texnologiyalar va qayta ishlash: quyosh panellari hamda *Trilliant* uslubidagi oqova (kulrang) suvni tualet uchun filtrlash tizimi.
  - Ikki pog'onali standart: O'zbekiston standarti (Asosiy) va Ilg'or Jahon/Yevropa tajribasi.
  - AutoCAD (DWG) andoza ko'rsatkichlari: 6x6m konstruktiv o'qlar to'ri, qavat balandliklari, devor qatlamlari chizmasi.
- **09:00 Ertalabki Yetkazish**: Ish kuni boshlanishida to'liq tayyorlangan ma'lumotnoma mutaxassisning Telegramiga yetkaziladi.
- **Ma'lumotnomani Darhol Ko'rish & Sinov Buyruqlari**:
  - Vazifa topshirilgach, foydalanuvchi darhol *"⏳ AI tahlil qilmoqda..."* xabarini oladi (kutish vaqtida Telegram qotib qolmaydi).
  - Tayyor bo'lgach, **"⚡ Ma'lumotnomani hoziroq ko'rish"** tugmasi orqali 09:00 ni kutmasdan natijani o'sha zahotiyoq ochish mumkin.
  - `/instant_dossier` — oxirgi tayyorlangan ma'lumotnomani istalgan paytda darhol chiqarish.
  - `/trigger_morning` — 09:00 yetkazish vazifasini hoziroq sinab ko'rish.
  - `/trigger_evening` — 19:00 kechki so'rov vazifasini hoziroq sinab ko'rish.

---

## 2. Kunlik Ishlash Sxemasi (Daily Workflow)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 19:00 — Kechki So'rov (Telegram Bot)                                   │
│ • Bot: "Ertaga qaysi loyiha ustida ishlaysiz?"                         │
│ • Mutaxassis loyiha nomi, bino turi va talablarini kiritadi.           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Tun bo'yi — AI Avtonom Tadqiqoti & Tahlili                             │
│ • SHNK/QMQ va shaharsozlik qoidalarini aniqlaydi.                      │
│ • Bozorlar va zavodlardan materiallar narxini tahlil qiladi.           │
│ • Yashil texnologiyalar va AutoCAD andozasini tayyorlaydi.             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 09:00 — Ertalabki Shpargalka Yetkazish                                 │
│ • Mutaxassis ishga kelganda tayyor texnik dossierni qabul qiladi.      │
│ • Tayyorgarlik ishlari 40–60% tayyor holda loyihalash boshlanadi.      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Texnologiyalar (Tech Stack)

- **Til va Muhit**: Python 3.11+, `uv` paket boshqaruvchisi.
- **Telegram Bot**: `aiogram 3.x` (FSM holatlari va inline tugmalar bilan).
- **Vazifalar Rejalashtiruvchisi**: `APScheduler` (Kechki 19:00 va Ertalabki 09:00 avtomatik cron triggers).
- **Sun'iy Intellekt**: Google Gemini API (`gemini-3.6-flash`).
- **Ma'lumotlar Bazasi**: SQLite (`sqlite+aiosqlite:///adad.db`, tashqi server yoki Docker talab etilmaydi).

---

## 4. O'rnatish va Ishga Tushirish (Quick Start)

### A. Sozlamalar (`.env`)
`.env` faylida quyidagi ma'lumotlar kiritilganiga ishonch hosil qiling:
```dotenv
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite+aiosqlite:///adad.db
LLM_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.6-flash
TIMEZONE=Asia/Tashkent
```

### B. Kutubxonalarni yangilash
```bash
uv sync
```

### C. Sinovdan o'tkazish (Smoke Test)
```bash
uv run python tests/smoke_test.py
```

### D. Botni ishga tushirish
```bash
uv run python main.py
```