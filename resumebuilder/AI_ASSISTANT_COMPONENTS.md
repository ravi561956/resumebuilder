# AI Assistant Component Coverage

The Django Admin AI Assistant is enabled for these content-writing fields:

## Resume
- Short Description
- Summary
- Skills
- Experience

## Journey
- Journey → Short Description
- Resume Journey → Description

## Profession
- Profession → Short Description

## Services
- Service → Description

## Testimonials
- Testimonial → Quote

## Excellence
- Excellence → Description

The assistant is injected into both standalone admin fields and Django TabularInline rows. It also handles dynamically added inline rows.

AI generation uses `/ai/generate/component/`, the existing AI provider priority/fallback system, user credit balance, and AIGeneration audit logging.

For normal users, ownership is resolved from the logged-in user and the user's Resume; users cannot use the assistant against another user's Resume/component.

After replacing files:

```bash
python manage.py check
python manage.py migrate
python manage.py runserver
```
