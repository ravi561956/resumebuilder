import pdfkit
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO


def generate_resume_pdf(resume, request):
    # ✅ Absolute image URL (works for PDF)
    image_url = None
    if resume.profile_image:
        image_url = request.build_absolute_uri(resume.profile_image.url)

    template_name = f"resume/pdf/{resume.pdf_template}.html"

    try:
        html = render_to_string(
            template_name,
            {
                "resume": resume,
                "image_url": image_url
            }
        )
    except Exception:
        # fallback template
        html = render_to_string(
            "resume/pdf/pdf1.html",
            {
                "resume": resume,
                "image_url": image_url
            }
        )

    config = None
    if getattr(settings, "WKHTMLTOPDF_PATH", None):
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_PATH)

    # ✅ PDF options (important for images + layout)
    options = {
        "enable-local-file-access": "",
        "encoding": "UTF-8",
        "quiet": "",
        "page-size": "A4",
        "margin-top": "10mm",
        "margin-right": "10mm"
    }
        # ✅ CREATE PDF
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    # ✅ RETURN BUFFER
    buffer = BytesIO(pdf)
    return buffer