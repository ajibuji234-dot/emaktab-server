# eMaktab Avto-Kirish & Faollikni Ta'minlash Veb-Ilovasi

Ota-onalar o'rniga **eMaktab.uz** (kundalik) tizimiga har kuni yoki har hafta avtomatik kirib beruvchi maxsus veb-sayt (panel).

---

## 🎯 Asosiy Imkoniyatlari

1. **Ko'p foydalanuvchilar hisobi:**
   - Bir vaqtning o'zida butun sinf, oila a'zolari yoki bir nechta farzandning ota-onalari hisoblarini qo'shish.
2. **Kunlik avtomatik reja (Scheduler):**
   - Tizim har kuni belgilangan soatlarda (masalan, ertalab `08:30` va kechqurun `18:00`) o'zi fonda eMaktabga kiradi va faollikni ro'yxatga oladi.
3. **Faollikni to'liq oshirish:**
   - Shunchaki login sahifasini ochib qo'ymaydi, balki `schools.emaktab.uz`, `feed` va profil sahifalarini ochib, eMaktab bazasida ota-onaning faolligini qayd etadi.
4. **Bloklanishdan himoya:**
   - Har bir hisob orasida tabiiy tanaffus (4-10 soniya) qiladi, bu eMaktab xavfsizlik filtrlari tomonidan spam sifatida aniqlanmasligini ta'minlaydi.
5. **Tezkor sinov tugmasi:**
   - Istalgan vaqtda bitta tugma orqali ("Kirish") hisobning login va paroli to'g'riligini va hozirgi faollikni tekshirib ko'rish mumkin.
6. **Batafsil jurnallar (Audit Logs):**
   - Qachon, kim uchun tizimga kirilgani va natijasi (muvaffaqiyatli yoki xatolik) saqlanib boradi.
7. **Xavfsizlik:**
   - Ma'lumotlar tashqi serverlarga ketmaydi, butunlay o'zingizning kompyuteringizdagi mahalliy SQLite bazasida saqlanadi.

---

## 🚀 Ishga Tushirish (Windows)

### 1-usul: Tayyor fayl orqali (Eng oson)
Papka ichidagi `run.bat` fayliga sichqoncha bilan ikki marta bosing. Dastur o'zi avtomatik ishga tushadi va brauzeringizda ochiladi.

### 2-usul: Buyruqlar satri (Terminal) orqali
1. Terminalda loyiha papkasiga o'ting:
   ```cmd
   cd C:\Users\SIROJ\.gemini\antigravity\scratch\emaktab-auto-web
   ```
2. Dasturni ishga tushiring:
   ```cmd
   .venv\Scripts\python.exe app.py
   ```
3. Brauzerda quyidagi manzilni oching:
   ```
   http://localhost:5000
   ```

---

## 🛠️ Qanday Foydalaniladi?

1. **Yangi hisob qo'shish:**
   - Asosiy paneldagi **"Yangi Hisob"** tugmasini bosing.
   - Ota-ona yoki o'quvchi ismini, eMaktab logini va parolini kiriting.
   - Kirish davriyligini tanlang (masalan, *Har kuni*).
2. **Tekshirish:**
   - Ro'yxatdagi hisob yonidagi **"Kirish"** tugmasini bosing. Tizim darhol eMaktabga ulanib ko'radi va natijani ko'rsatadi.
3. **Sozlamalar:**
   - **"Sozlamalar"** bo'limida avtomatik kirish soatlarini (masalan, ertalab va kechqurun) o'zingizga qulay qilib o'zgartirishingiz mumkin.
