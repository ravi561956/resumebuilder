from django.db import models
from django.contrib.auth.models import User


# -----------------------------------
# MODERATION VIOLATIONS
# -----------------------------------

class ModerationViolation(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    resume = models.ForeignKey(
        'resume.Resume',
        on_delete=models.CASCADE
    )

    section = models.CharField(
        max_length=255
    )

    reason = models.TextField()

    blocked_text = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.section}"
    

class AIProvider(models.Model):

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("gemini", "Google Gemini"),
        ("anthropic", "Anthropic Claude"),
        ("deepseek", "DeepSeek"),
        ("grok", "Grok"),
        ("azure_openai", "Azure OpenAI"),
        ("ollama", "Ollama"),
    ]

    name = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        unique=True
    )

    is_active = models.BooleanField(
        default=False
    )

    api_key = models.TextField(
        blank=True,
        null=True
    )

    model_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    base_url = models.URLField(
        blank=True,
        null=True
    )

    priority = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["priority"]

    def __str__(self):
        return f"{self.get_name_display()} - {self.model_name}"


class ModerationSetting(models.Model):

    moderation_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable moderation globally."
    )

    keyword_filter_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable keyword filtering."
    )

    bad_keywords = models.TextField(
        blank=True,
        default=(
            "escort\n"
            "porn\n"
            "pornographic\n"
            "call girl\n"
            "sex service\n"
            "sex worker\n"
            "adult service\n"
            "adult content\n"
            "nude\n"
            "nudes\n"
            "nudity\n"
            "naked photos\n"
            "xxx\n"
            "nsfw\n"
            "hardcore\n"
            "hookup\n"
            "onlyfans\n"
            "camgirl\n"
            "webcam sex\n"
            "bdsm\n"
            "fetish\n"
            "threesome\n"
            "twosome\n"
            "gangbang\n"
            "swinging\n"
            "swingers\n"
            "swapping partners\n"
            "wife swap\n"
            "sugar daddy\n"
            "sugar baby"
        ),
        help_text=(
            "One keyword per line. Deliberately excludes sexual-orientation "
            "or gender-identity words (e.g. 'gay', 'lesbian') since those are "
            "legitimate identity terms, not indicators of explicit content â "
            "blocking them would wrongly flag genuine resumes/bios."
        )
    )

    active_provider = models.ForeignKey(
        AIProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="AI provider used for moderation."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "AI Moderation Setting"
        verbose_name_plural = "AI Moderation Setting"

    def __str__(self):
        return "AI Moderation Settings"