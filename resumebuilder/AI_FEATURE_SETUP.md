# AI Content + Credit Monetization

## What was added

- `apps.ai_content` Django app.
- Super-admin controlled AI content feature flag.
- Super-admin controlled paid/free AI mode.
- Configurable AI packages: tokens/credits, INR price and active status.
- Per-user credit balance, purchase history, generation history and credit transactions.
- Razorpay purchase flow with server-side signature verification and webhook support.
- AI assistant inside the Resume Django Admin change form for:
  - Short Description
  - Summary
  - Skills
  - Experience
  - Education
- AI cover-letter generator.
- Cover letter is **free for normal users by default** and can be changed to paid by super-admin.
- AI provider credentials/configuration are kept under the existing AI Provider admin configuration.

## Super-admin workflow

1. Login at `/admin/` as super-admin.
2. Open **AI Content & Credits**.
3. Open **AI Content Setting**:
   - `AI content enabled`: master switch for resume AI.
   - `Paid AI required`: when ON, users need purchased credits.
   - `Default generation cost`: fallback charge when the provider does not return token usage.
   - `Max output tokens`: generation limit.
4. Create one or more **AI Packages** such as `Starter`, `Professional`, `Enterprise` with your own token amount and INR price.
5. Open **Cover Letter Setting** and choose whether the feature is enabled and whether it is free for normal users.
6. Open **AI Provider** and configure an active OpenAI or Azure OpenAI provider/model.

## Payment setup

Set these environment variables in the server environment:

```text
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
AZURE_OPENAI_API_VERSION=2024-10-21
```

Configure the Razorpay webhook endpoint:

```text
/ai/payment/webhook/
```

Recommended events: `payment.captured` and `order.paid`.

## Install and migrate

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

## User workflow

1. User opens **AI Content & Credits** from the dashboard.
2. User sees available packages and current AI credit balance.
3. User purchases a package using Razorpay.
4. After verified payment, purchased credits are added to that user's balance.
5. In the Resume Admin content form, the AI Content Assistant appears for the supported content fields.
6. Resume AI consumes actual provider-reported tokens when available.
7. Cover letter is free by default and does not consume credits; if the super-admin turns off `free_for_users`, it consumes purchased credits.

## Important

The uploaded project did not have Django installed in the execution environment, so Django's runtime checks/migrations could not be executed here. The new Python modules were syntax-checked with `compileall`. Run the migration and Django checks in your project's virtual environment before deployment.

## Payment credential security and development safety

Payment credentials configured by Superadmin are encrypted at rest in the database using a key derived from `DJANGO_SECRET_KEY`. Keep `DJANGO_SECRET_KEY` stable; changing it will make existing encrypted payment credentials unreadable.

In the Django admin, payment credential fields are masked. When editing an existing gateway, leave a credential blank to retain the existing encrypted value.

For development, Razorpay `Live / Production` mode is blocked while `DEBUG=True`. Use Razorpay Test/Sandbox credentials. This prevents accidental real charges from a development server.

Run the new migration after installing dependencies:

```bash
python manage.py migrate
```
