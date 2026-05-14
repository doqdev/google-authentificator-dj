# Google Authenticator Django Demo

To‘liq ishlaydigan namunaviy loyiha:
- Django default auth (register/login/logout)
- Google Authenticator bilan TOTP 2FA
- Docker Compose (Django + PostgreSQL)
- `.env` orqali sozlanadigan konfiguratsiya

## 1) Loyiha tuzilmasi

- `config/` — Django project sozlamalari (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`)
- `accounts/` — auth va 2FA app:
  - `models.py` — `TwoFactorProfile` (secret + enable holati)
  - `views.py` — register/login/profile/2FA challenge logikasi
  - `forms.py` — register/login/TOTP formalar
  - `management/commands/init_superuser.py` — env orqali superuser yaratish
  - `tests.py` — auth va 2FA oqimi testlari
- `templates/` — oddiy UI:
  - `registration/register.html`
  - `registration/login.html`
  - `accounts/profile.html`
  - `accounts/two_factor_challenge.html`
- `Dockerfile` — Django image
- `docker-compose.yml` — web + postgres
- `entrypoint.sh` — migrate + collectstatic + superuser init
- `requirements.txt` — dependency ro‘yxati
- `.env.example` — env namuna

## 2) Talablar

- Docker + Docker Compose
  (yoki lokal ishga tushirish uchun Python 3.12)

## 3) O‘rnatish (Docker Compose)

1. Repository clone qiling va papkaga kiring.
2. `.env.example` dan `.env` yarating:

```bash
cp .env.example .env
```

3. Kerak bo‘lsa `.env` qiymatlarini o‘zgartiring.
4. Loyihani ishga tushiring:

```bash
docker compose up --build
```

5. App: `http://localhost:8000`
6. Admin: `http://localhost:8000/admin`

`entrypoint.sh` avtomatik:
- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`
- `python manage.py init_superuser`

## 4) Lokal ishga tushirish (ixtiyoriy)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Lokalda tez ishga tushirish uchun `DB_ENGINE=sqlite` qilib qo‘yishingiz mumkin.

## 5) 2FA ishlash oqimi

1. `Register` sahifasidan user yaratiladi.
2. `Login` sahifasida username/password bilan kiriladi.
3. `Profile` sahifasida:
   - `Generate 2FA secret` bosiladi
   - QR chiqadi (Google Authenticator bilan scan qilinadi)
   - App’dan 6 xonali kod kiritib `Verify and enable` qilinadi
4. Endi login paytida:
   - Parol to‘g‘ri bo‘lsa ham, 2FA yoqilgan bo‘lsa darhol kiritmaydi
   - `2FA challenge` sahifasiga o‘tkazadi
   - To‘g‘ri TOTP kod kiritilgandagina profilga kiradi

### Yangi foydalanuvchi uchun sodda yo‘riqnoma (secret/QR qayerda?)

1. Avval `Register` qiling, keyin `Login` qiling.
2. `Profile` (`/profile/`) sahifasiga kiring.
3. `Generate 2FA secret` ni bosing:
   - Shu sahifaning o‘zida `QR code` chiqadi.
   - Shu sahifaning o‘zida `Backup key` (bu sizning **secret** kalitingiz) ko‘rinadi.
4. Google Authenticator ilovasida:
   - `+` bosing → `Scan a QR code` ni tanlab QR’ni skaner qiling, yoki
   - `Enter setup key` orqali `Backup key` (secret) ni qo‘lda kiriting.
5. Ilovadagi 6 xonali kodni `Profile` sahifasidagi `Verify and enable` formiga kiriting.
6. Kod to‘g‘ri bo‘lsa 2FA yoqiladi (`Enabled` holati chiqadi).
7. Keyingi loginlarda:
   - Avval username/password,
   - So‘ng `/2fa/challenge/` sahifasida Google Authenticator kodini kiritasiz.

## 6) Muhim ENV parametrlar

`.env.example` ichida:
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_TOTP_ISSUER`
- DB: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- Superuser: `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`

## 7) Testlar

```bash
python manage.py test
```

Qamrov:
- register ishlashi
- 2FA bo‘lmasa oddiy login ishlashi
- 2FA yoqilgan bo‘lsa login challenge talab qilishi
- to‘g‘ri TOTP kod bilan login yakunlanishi

## 8) FAQ: Google’dan credential olish kerakmi?

Qisqa javob: **yo‘q, TOTP 2FA uchun Google API credential kerak emas**.

- Google Authenticator bu Google API’ga bog‘langan servis emas; u **ochiq TOTP standarti (RFC 6238)** bo‘yicha kod yaratadi.
- Shu sababli `pyotp` + `qrcode` bilan ishlaganda Google Developer Console’dan `api_key`, `client_id`, `client_secret` yoki token olish talab qilinmaydi.
- Foydalanuvchi server bergan **secret** va **QR (otpauth URI)** ni olib, Google Authenticator, Authy, Microsoft Authenticator kabi istalgan TOTP ilovasida ishlata oladi.
- Google credential/OAuth faqat **Google account bilan kirish (federated login / Sign in with Google)** qilmoqchi bo‘lsangiz kerak bo‘ladi.
