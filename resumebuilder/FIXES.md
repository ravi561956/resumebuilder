# Resume Builder — Audit & Fixes

I could not `pip install`/run this project in my sandbox (no network access
here), so everything below was verified statically: full `py_compile` across
every `.py` file (no syntax errors), plus a custom undefined-name checker,
plus manual code review of the core app (views, urls, forms, models, utils,
whatsapp/social/moderation apps).

## Bugs fixed

1. **Broken PDF preview URL** (`resume/urls.py`)
   `path('resume:preview-pdf/<int:pk>/', ...)` produced a literal, invalid
   URL path. Changed to `path('resume/preview-pdf/<int:pk>/', ...)`. This is
   what the "Preview PDF" link in the Django admin (`resume/admin.py`)
   depends on via `reverse('resume_pdf_preview', ...)`.

2. **Guaranteed crash on every resume save** (`resume/forms.py`)
   `ResumeForm.clean()` called `validate_resume_content(instance)` and
   caught `ValidationError`, but neither name was imported — every resume
   edit would raise `NameError`. Added:
   ```python
   from django.core.exceptions import ValidationError
   from apps.moderation.services import validate_resume_content
   ```

3. **Login page unreachable** (`resume/views.py`, `user_login`)
   Any `GET /login/` was unconditionally redirected to `/admin`, so the
   fully-built `auth/login.html` page could never actually be shown. GET
   requests now render that template as intended.

4. **Crash when a WhatsApp OTP expires** (`resume/views.py`,
   `resume/urls.py`)
   `verify_whatsapp_otp` redirected to `'resend_whatsapp_otp'`, but no such
   URL or view existed — this raised `NoReverseMatch`. Added a
   `resend_whatsapp_otp` view (mirroring the existing `resend_otp` for
   email) and registered its URL.

5. **Leaked live API key / unsafe import** (`resume/llm.py`)
   The file hardcoded a Google Gemini API key and made a live network call
   at *import time*. It isn't referenced anywhere else in the project.
   Rewritten as an opt-in `ask_gemini()` helper that reads
   `GEMINI_API_KEY` from the environment and only calls the API when
   explicitly invoked. **You should rotate/revoke the key that was in the
   original file, since it was committed in plaintext.**

6. **Unusable `requirements.txt`**
   The original file was a raw `pip freeze` of a full Windows Anaconda
   install (thousands of unrelated packages, `file:///C:/...` paths) —
   not installable on any other machine. Replaced with a minimal list
   matching what the project actually imports (Django, django-ckeditor-5,
   Pillow, beautifulsoup4, python-docx, pdfkit, requests, twilio, openai,
   social-auth-app-django). Also added `django-ckeditor` — it's not used
   directly anymore, but migration `resume/migrations/0031_*.py` still
   imports `ckeditor_uploader.fields` from it, so a fresh `migrate` needs
   it installed even though current models use `django-ckeditor-5`.

7. **Hardcoded secrets in `settings.py`**
   `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` were hardcoded (with
   `ALLOWED_HOSTS = ['*']`, i.e. wide open). Now read from
   `DJANGO_SECRET_KEY` / `DJANGO_DEBUG` / `DJANGO_ALLOWED_HOSTS` env vars,
   falling back to the original dev-only values so local behavior is
   unchanged. Added `.env.example` documenting these plus `OPENAI_API_KEY`
   / `GEMINI_API_KEY`.

## Known limitations / things I could not verify

- I could not actually boot the Django dev server or run `manage.py
  migrate`/`check` here (no network to install Django). Please run:
  ```bash
  python -m venv venv
  source venv/bin/activate   # or venv\Scripts\activate on Windows
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver
  ```
  and let me know if anything surfaces at runtime — I'm happy to keep
  debugging from there.
- `wkhtmltopdf` (used by `resume/utils/resume_pdf.py` via `pdfkit`) must be
  installed separately on the host OS; it's a system binary, not a Python
  package. `settings.WKHTMLTOPDF_PATH` already points at the common
  Linux/Windows install locations.
- The moderation service (`apps/moderation/services.py`) re-scans the
  *entire* resume (every section, twice for testimonials — there's a
  duplicated block) on every single save via the OpenAI Moderation API.
  This works but is inefficient/costly; I left the logic as-is since it's
  not broken, just worth knowing about.
- `apps/whatsapp/urls.py` is empty and not included in the main URLconf —
  `apps/whatsapp/views/admin_views.py` appears to be an unfinished/unwired
  admin panel feature. Left untouched since it's not on any currently
  broken code path.

## AI Content Monetization

Added `apps.ai_content` for:
- Super-admin controlled AI content enable/disable and paid/free mode.
- Configurable AI credit packages (token/credit amount, INR price, active status).
- Per-user AI credit balance, purchases, transactions and generation audit logs.
- Razorpay order creation, payment signature verification and webhook support.
- AI assistant in the Django Resume change form for Short Description, Summary, Skills, Experience and Education.
- AI cover-letter generator; free for normal users by default and switchable by super-admin.

Setup:
1. Install `razorpay` from `requirements.txt`.
2. Configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` and `RAZORPAY_WEBHOOK_SECRET`.
3. Configure an active supported AI provider in the existing Moderation > AI Providers screen. OpenAI and Azure OpenAI are supported for generation.
4. Run `python manage.py migrate`.
5. As super-admin, create AI Packages and configure AI Content Setting / Cover Letter Setting in Django admin.
6. Set the Razorpay webhook to `/ai/payment/webhook/` and enable payment captured/order paid events.
