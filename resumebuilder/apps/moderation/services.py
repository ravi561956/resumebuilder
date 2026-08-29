from openai import OpenAI
from django.conf import settings
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from .utils import (get_moderation_settings, get_bad_keywords)
from .models import ModerationViolation
from django.core.mail import send_mail
from .models import ModerationViolation

        
def _resolve_resume(instance):
    """Return the Resume related to a Resume or any supported child component."""
    from resume.models import Resume

    if isinstance(instance, Resume):
        return instance

    # Direct FK used by most component models.
    direct = getattr(instance, "resume", None)
    if isinstance(direct, Resume):
        return direct

    # Walk common parent relationships (Skill -> SkillCategory -> Resume, etc.).
    for relation in ("category", "certificate", "section", "journey"):
        parent = getattr(instance, relation, None)
        if parent is not None:
            resolved = _resolve_resume(parent)
            if resolved is not None:
                return resolved

    return None


def validate_resume_content(instance):
    resume = _resolve_resume(instance)
    # Child components may be created before their Resume relation is selected.
    # There is nothing to scan in that case, but it must never crash with an
    # AttributeError such as TestimonialSection.name.
    if resume is None:
        return

    moderation = scan_resume(resume)

    if moderation["blocked"]:
    
        raise ValidationError(
            f"{moderation['section']}: "
            f"{moderation['reason']}"
        )
           
def get_openai_client():   
    moderation_settings = get_moderation_settings()
    provider = moderation_settings.active_provider
    if not provider:
        raise ValidationError(
            "No AI moderation provider configured."
        )
    api_key = provider.api_key
    if not api_key:
        api_key = settings.OPENAI_API_KEY

    return OpenAI(
        api_key=api_key
    )
# -----------------------------------
# CLEAN CKEDITOR HTML
# -----------------------------------
def clean_html(html_content):

    if not html_content:
        return ""

    soup = BeautifulSoup(
        html_content,
        "html.parser"
    )

    return soup.get_text(separator=" ")

# -----------------------------------
# AI MODERATION
# -----------------------------------
def moderate_resume_content(text):
    text = (text or "").strip()

    if not text:
        return {
            "blocked": False,
            "error": False,
            "reason": "",
        }

    moderation_settings = get_moderation_settings()

    # Moderation disabled by admin
    if not moderation_settings.moderation_enabled:
        return {
            "blocked": False,
            "error": False,
            "reason": "Moderation is disabled.",
        }

    # -----------------------------------
    # KEYWORD FILTER
    # -----------------------------------
    lower_text = text.lower()

    if moderation_settings.keyword_filter_enabled:
        bad_keywords = get_bad_keywords()

        for word in bad_keywords:
            if word.lower() in lower_text:
                return {
                    "blocked": True,
                    "error": False,
                    "reason": f"Blocked keyword detected: {word}",
                }

    # Ignore very small content
    if len(text) < 2:
        return {
            "blocked": False,
            "error": False,
            "reason": "",
        }

    provider = moderation_settings.active_provider

    if not provider:
        return {
            "blocked": False,
            "error": True,
            "reason": "No AI moderation provider configured.",
        }

    try:
        client = get_openai_client()

        response = client.moderations.create(
            model=provider.model_name,
            input=text,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)

        logger.exception(
            "AI moderation failed: %s",
            str(e),
        )

        # IMPORTANT:
        # API failure is NOT a content violation.
        return {
            "blocked": False,
            "error": True,
            "reason": str(e),
        }

    result = response.results[0]

    # -----------------------------------
    # ACTUAL CONTENT VIOLATION
    # -----------------------------------

    if (
        result.categories.sexual
        or result.categories.sexual_minors
    ):
        return {
            "blocked": True,
            "error": False,
            "reason": "AI detected sexual/adult content.",
        }

    return {
        "blocked": False,
        "error": False,
        "reason": "",
    }

def log_violation(
    resume,
    section,
    field,
    reason
):
    return ModerationViolation.objects.create(
        user=resume.user,
        resume=resume,
        section=section,
        reason=reason
    )
    

def get_violation_count(resume):
    
    return ModerationViolation.objects.filter(
        resume=resume
    ).count()
    
# -----------------------------------
# CENTRAL RESUME SCANNER
# -----------------------------------
def scan_resume(resume):
    # -----------------------------------
    # BASIC INFORMATION
    # -----------------------------------
    basic_info_text = " ".join([
        resume.name or "",
        resume.title or "",
        resume.position or "",
        resume.address or "",
        resume.website or "",
        resume.tags or "",
        resume.tag_line or "",
        resume.short_desc or "",
        resume.summary or "",
        resume.skills or "",
        resume.experience or "",
        resume.education or "",
    ])
    result = moderate_resume_content(
        basic_info_text
    )

    if result["blocked"]:
        return {
            "blocked": True,
            "section": "Basic Information",
            "reason": result["reason"]
        }

    # -----------------------------------
    # SHORT DESCRIPTION
    # -----------------------------------

    result = moderate_resume_content(
        clean_html(resume.short_desc)
    )

    if result["blocked"]:
        return {
            "blocked": True,
            "section": "Short Description",
            "reason": result["reason"]
        }

    # -----------------------------------
    # SUMMARY
    # -----------------------------------

    result = moderate_resume_content(
        clean_html(resume.summary)
    )

    if result["blocked"]:
        return {
            "blocked": True,
            "section": "Summary",
            "reason": result["reason"]
        }

    # -----------------------------------
    # SKILLS
    # -----------------------------------

    result = moderate_resume_content(
        clean_html(resume.skills)
    )

    if result["blocked"]:
        return {
            "blocked": True,
            "section": "Skills",
            "reason": result["reason"]
        }

    # -----------------------------------
    # RESUME SOCIALS
    # -----------------------------------
    for social in resume.socials.all():
        result = moderate_resume_content(f"{social.platform} {social.url}")
        if result["blocked"]:
            return {
                "blocked": True,
                "section": "Social Links",
                "reason": result["reason"]
            }

    # -----------------------------------
    # FLOATING CARDS
    # -----------------------------------
    for card in resume.floating_cards.all():
        result = moderate_resume_content(f"{card.title}")
        if result["blocked"]:
            return {
                "blocked": True,
                "section": "card",
                "reason": result["reason"]
            }

    # -----------------------------------
    # RESUME SKILLS
    # -----------------------------------
    for skill in resume.skills_grid.all():
        result = moderate_resume_content(f"{skill.title} {clean_html(skill.description)}")
        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Skill: {skill.title}",
                "reason": result["reason"]
            }

    # -----------------------------------
    # JOURNEY
    # -----------------------------------
    for journey in resume.journeys.all():
        result = moderate_resume_content(f"{journey.year} {clean_html(journey.description)}")
        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Journey: {journey.year}",
                "reason": result["reason"]
            }

    # -----------------------------------
    # SKILL CATEGORY
    # -----------------------------------
    for category in resume.skill_categories.all():
        result = moderate_resume_content(
            category.title or ""
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Skill Category ({category.title})",
                "reason": result["reason"]
            }

        for skill in category.skills.all():
            result = moderate_resume_content(
                skill.name or ""
            )
            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": f"Skill ({skill.name})",
                    "reason": result["reason"]
                }
    # -----------------------------------
    # PROFESSIONS
    # -----------------------------------
    for profession in resume.professions.all():
    
        profession_text = " ".join([
            profession.title or "",
            clean_html(profession.short_desc),
        ])

        result = moderate_resume_content(
            profession_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Profession ({profession.title})",
                "reason": result["reason"]
            }
            
    # -----------------------------------
    # JOURNEY SECTION
    # -----------------------------------
    for journey in resume.journey.all():

        journey_text = " ".join([
            journey.title or "",
            clean_html(journey.short_desc),
        ])

        result = moderate_resume_content(
            journey_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Journey ({journey.title})",
                "reason": result["reason"]
            }

        for excellence in journey.excellences.all():

            excellence_text = " ".join([
                excellence.title or "",
                excellence.company or "",
                excellence.date_range or "",
                clean_html(excellence.description),
            ])

            result = moderate_resume_content(
                excellence_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": f"Excellence ({excellence.title})",
                    "reason": result["reason"]
                }
                
    # -----------------------------------
    # SERVICES
    # -----------------------------------
    for service_section in resume.servicesection.all():

        service_section_text = " ".join([
            service_section.title or "",
            clean_html(service_section.subtitle),
        ])

        result = moderate_resume_content(
            service_section_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": (
                    f"Service Section ({service_section.title})"
                ),
                "reason": result["reason"]
            }

        for service in service_section.services.all():

            service_text = " ".join([
                service.title or "",
                clean_html(service.description),
            ])

            result = moderate_resume_content(
                service_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": f"Service ({service.title})",
                    "reason": result["reason"]
                }
                
    # -----------------------------------
    # PORTFOLIO
    # -----------------------------------
    for portfolio in resume.portfolio_sections.all():

        portfolio_text = " ".join([
            portfolio.title or "",
            portfolio.subtitle or "",
        ])

        result = moderate_resume_content(
            portfolio_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": f"Portfolio ({portfolio.title})",
                "reason": result["reason"]
            }

        for item in portfolio.items.all():

            item_text = " ".join([
                item.title or "",
                item.project_url or "",
            ])

            result = moderate_resume_content(
                item_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": (
                        f"Portfolio Item ({item.title})"
                    ),
                    "reason": result["reason"]
                }
    # -----------------------------------
    # TESTIMONIALS
    # -----------------------------------
    for testimonial_section in resume.testimonial_sections.all():

        section_text = " ".join([
            testimonial_section.title or "",
            testimonial_section.subtitle or "",
        ])

        result = moderate_resume_content(
            section_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": (
                    f"Testimonial Section ({testimonial_section.title})"
                ),
                "reason": result["reason"]
            }

        for testimonial in testimonial_section.testimonials.all():

            testimonial_text = " ".join([
                clean_html(testimonial.quote),
                testimonial.author_name or "",
                testimonial.author_role or "",
                testimonial.source or "",
            ])

            result = moderate_resume_content(
                testimonial_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": (
                        f"Testimonial ({testimonial.author_name})"
                    ),
                    "reason": result["reason"]
                }

    # -----------------------------------
    # TESTIMONIALS
    # -----------------------------------
    for testimonial_section in resume.testimonial_sections.all():

        section_text = " ".join([
            testimonial_section.title or "",
            testimonial_section.subtitle or "",
        ])

        result = moderate_resume_content(
            section_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": (
                    f"Testimonial Section ({testimonial_section.title})"
                ),
                "reason": result["reason"]
            }

        for testimonial in testimonial_section.testimonials.all():

            testimonial_text = " ".join([
                clean_html(testimonial.quote),
                testimonial.author_name or "",
                testimonial.author_role or "",
                testimonial.source or "",
            ])

            result = moderate_resume_content(
                testimonial_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": (
                        f"Testimonial ({testimonial.author_name})"
                    ),
                    "reason": result["reason"]
                }

    # -----------------------------------
    # CONTACT SECTION
    # -----------------------------------
    for contact in resume.contact_sections.all():

        contact_text = " ".join([
            contact.title or "",
            clean_html(contact.subtitle),
            clean_html(contact.description),
            contact.location or "",
            contact.phone_numbers or "",
            contact.email_addresses or "",
        ])

        result = moderate_resume_content(
            contact_text
        )

        if result["blocked"]:
            return {
                "blocked": True,
                "section": (
                    f"Contact Section ({contact.title})"
                ),
                "reason": result["reason"]
            }

        for message in contact.messages.all():

            message_text = " ".join([
                message.name or "",
                message.email or "",
                message.subject or "",
                clean_html(message.message),
            ])

            result = moderate_resume_content(
                message_text
            )

            if result["blocked"]:
                return {
                    "blocked": True,
                    "section": (
                        f"Contact Message ({message.subject})"
                    ),
                    "reason": result["reason"]
                }
    return {
        "blocked": False,
        "reason": ""
    }