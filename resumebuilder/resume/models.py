from django.db import models
from django.conf import settings
from .utils.image_utils import resize_image
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.moderation.services import validate_resume_content


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    subdomain = models.SlugField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    THEME_CHOICES = (
        #  ('geeky-nextjs-1.0.0', 'Theme A - Geeky'),
        ('Style', 'Theme A - Style'),
        ('iPortfolio-1.0.0', 'Theme B - Iportfolio'),
        ('satner-master', 'Theme C - Satner'),
        ('jackson-master', 'Theme D - jackson'),
        # ('Typefolio-1.0.0', 'Theme D - Typefolio'),
        ('meyawo-1.0.0', 'Theme E - Meyawo'),
        ('MyResume-1.0.0', 'Theme F - MyResume'),
        ('resume-bootstrap4-master', 'Theme G - resume'),
        ('FolioOne', 'Theme D - FolioOne'),
        # Add more themes here
    )
    PDF_TEMPLATE_CHOICES = [
        ('pdf1', 'Modern Sidebar'),
        ('pdf2', 'ATS Friendly'),
        ('pdf3', 'Minimal ATS'),
    ]
    position = models.CharField(default='Senior technical lead', max_length=250)
    address = models.CharField(default='Noida,India', max_length=250)
    website = models.CharField(blank=True,default='', max_length=250)
    tags = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Comma separated tags (e.g. Python, Django, React)"
    )
    tag_line = models.CharField(
        max_length=150,
        blank=True,
        default=''
        )
    pdf_template = models.CharField(
        max_length=20,
        choices=PDF_TEMPLATE_CHOICES,
        default='pdf1'
    )
    short_desc = CKEditor5Field('Short Description', blank=True, config_name='default')

    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='banner/', blank=True, null=True)

    summary = CKEditor5Field('Summary', blank=True, config_name='default')
    skills = CKEditor5Field('Skills', blank=True, config_name='default')
    experience = CKEditor5Field('Experience', blank=True, config_name='default')
    education = CKEditor5Field('Education', blank=True, config_name='default')

    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='meyawo-1.0.0')

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def tag_string(self):
        return ', '.join(self.tag_list())
    
    def skill_list(self):
        return self.skills.split(',')

    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        return settings.MEDIA_URL + 'defaults/default_avatar.png'

    @property
    def banner_image_url(self):
        if self.banner_image:
            return self.banner_image.url
        return settings.MEDIA_URL + 'defaults/default_banner.png'

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.profile_image:
            resize_image(self.profile_image.path, (300, 300))
        if self.banner_image:
            resize_image(self.banner_image.path, (1600, 400))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ResumeStat(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='stats',
        on_delete=models.CASCADE
    )
    icon_class = models.CharField(
        max_length=50,
        default='',
        help_text="Bootstrap icon class e.g. bi bi-trophy"
    )
    value = models.PositiveIntegerField(help_text="Number value (e.g. 150)")
    label = models.CharField(max_length=100, help_text="Label (e.g. Projects Completed)")
    aos_delay = models.PositiveIntegerField(default=300)
    order = models.PositiveIntegerField(default=0)
    
    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.value} - {self.label}"
     
# For social media
class ResumeSocial(models.Model):
    PLATFORM_CHOICES = (
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('website', 'Website'),
        ('other', 'Other'),
    )

    resume = models.ForeignKey(
        Resume,
        related_name='socials',
        on_delete=models.CASCADE
    )
    platform = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    url = models.URLField()
    icon_class = models.CharField(
        max_length=50,
        help_text="Icon class e.g. ti-twitter, ti-linkedin, fa fa-github"
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.platform} - {self.url}"

#Floating card
class ResumeFloatingCard(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='floating_cards',
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=100,
        help_text="Text shown under icon (e.g. UI/UX Design)"
    )

    icon_class = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class (e.g. bi bi-palette)"
    )

    card_class = models.CharField(
        max_length=50,
        help_text="CSS class (e.g. card-1, card-2)"
    )

    aos_animation = models.CharField(
        max_length=50,
        default='zoom-in',
        help_text="AOS animation (e.g. zoom-in, fade-up)"
    )

    aos_delay = models.PositiveIntegerField(
        default=300,
        help_text="Animation delay in ms (300, 400, 500)"
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

#Resume skills
class ResumeSkill(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='skills_grid',
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=100)
    description = CKEditor5Field('Description', config_name='default')

    icon_class = models.CharField(
        max_length=50,
        help_text="Icon class e.g. bi bi-palette, bi bi-code-slash"
    )

    aos_animation = models.CharField(
        max_length=30,
        default='zoom-in',
        help_text="AOS animation type"
    )
    aos_delay = models.PositiveIntegerField(
        default=400,
        help_text="Animation delay in ms (400, 450, 500)"
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

#Resume education
class ResumeJourney(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='journeys',
        on_delete=models.CASCADE
    )

    year = models.CharField(
        max_length=10,
        help_text="Year or range e.g. 2019 or 2020-2022"
    )

    description = CKEditor5Field('Description', config_name='default')

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()    
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.year} - {self.description[:30]}"

#skills category with percentage
class SkillCategory(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='skill_categories',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100)  # Frontend Development
    icon_class = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class e.g. bi bi-code-slash"
    )
    aos_delay = models.PositiveIntegerField(default=200)
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Skill(models.Model):
    category = models.ForeignKey(
        SkillCategory,
        related_name='skills',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)  # HTML/CSS
    percentage = models.PositiveIntegerField()  # 95
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

#Profession
class Profession(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='professions',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=100,null=True,blank=True)
    short_desc = CKEditor5Field('Short Description', config_name='default')

    resume_stats = models.ManyToManyField(
        ResumeStat,
        related_name='professions'
    )
    icon_class = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class e.g. bi bi-code-slash"
    )
    aos_delay = models.PositiveIntegerField(default=200)
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

#certification
class Certification(models.Model):
    certificate = models.ForeignKey(
        Profession,
        related_name='certifications',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100)
    certificate_image = models.ImageField(upload_to='certificate/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    @property
    def certificate_image_url(self):
        if self.certificate_image:
            return self.certificate_image.url
        return settings.MEDIA_URL + 'defaults/default_avatar.png'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.certificate_image:
            resize_image(self.certificate_image.path, (300, 300))

    def __str__(self):
        return f"{self.title}"
    
class Journey(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='journey',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=100,null=True,blank=True)
    short_desc = CKEditor5Field('Short Description', config_name='default')

    icon_class = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class e.g. bi bi-code-slash"
    )
    aos_delay = models.PositiveIntegerField(default=200)
    order = models.PositiveIntegerField(default=0)
    
    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
    
class Excellence(models.Model):
    journey = models.ForeignKey(
        Journey,
        related_name="excellences",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=150)  # Technical Director
    company = models.CharField(max_length=150)  # Proin Corporation
    date_range = models.CharField(max_length=50)  # 2022 - Present

    description = CKEditor5Field('Short Paragraph Description', config_name='default')


    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} @ {self.company}"

class ServiceSection(models.Model):
    resume = models.ForeignKey(
        Resume,
        related_name='servicesection',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=100,
        default="Services"
    )
    subtitle = CKEditor5Field('Service Sub Title', config_name='default')
    aos_delay = models.PositiveIntegerField(default=200)
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Service(models.Model):
    section = models.ForeignKey(
        ServiceSection,
        related_name="services",
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=150)
    description = CKEditor5Field('Short Paragraph Description', config_name='default')


    icon_class = models.CharField(
        max_length=50,
        help_text="Bootstrap icon class e.g. bi bi-layers"
    )

    learn_more_url = models.URLField(
        blank=True,
        null=True
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
    
class PortfolioSection(models.Model):
    resume = models.ForeignKey(
        'Resume',
        related_name='portfolio_sections',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=100, default="Portfolio")
    subtitle = models.TextField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    def __str__(self):
        return self.title


class PortfolioCategory(models.Model):
    section = models.ForeignKey(
        PortfolioSection,
        related_name='categories',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=50)
    slug = models.SlugField(
        help_text="Used for frontend filtering (e.g. uiux, development)"
    )
    order = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PortfolioItem(models.Model):
    section = models.ForeignKey(
        PortfolioSection,
        related_name='items',
        on_delete=models.CASCADE
    )
    categories = models.ManyToManyField(
        PortfolioCategory,
        related_name='items'
    )

    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='portfolio/')
    project_url = models.URLField(blank=True, null=True)

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class TestimonialSection(models.Model):
    resume = models.ForeignKey(
        'Resume',
        related_name='testimonial_sections',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=100, default="Testimonials")
    subtitle = models.TextField()

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=4.8
    )

    total_reviews = models.PositiveIntegerField(default=230)

    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        validate_resume_content(self)
        
    def __str__(self):
        return self.title


class Testimonial(models.Model):
    section = models.ForeignKey(
        TestimonialSection,
        related_name='testimonials',
        on_delete=models.CASCADE
    )

    quote = CKEditor5Field('Quote', config_name='default')

    rating = models.PositiveSmallIntegerField(
        default=5,
        help_text="1 to 5 stars"
    )

    author_name = models.CharField(max_length=100)
    author_role = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    author_image = models.ImageField(
        upload_to='testimonials/',
        blank=True,
        null=True
    )

    source = models.CharField(
        max_length=100,
        help_text="e.g. The New York Times, Goodreads"
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.author_name} – {self.source}"


class ReviewPlatform(models.Model):
    section = models.ForeignKey(
        TestimonialSection,
        related_name='platforms',
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=50)
    url = models.URLField(blank=True, null=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    def __str__(self):
        return self.name
    
class FAQSection(models.Model):
    resume = models.ForeignKey(
        'Resume',
        related_name='faq_sections',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=150,
        default="Frequently Asked Questions"
    )
    subtitle = models.TextField(
        help_text="Short description under section title"
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    section = models.ForeignKey(
        FAQSection,
        related_name='faqs',
        on_delete=models.CASCADE
    )

    question = CKEditor5Field('Question', config_name='default')
    answer = CKEditor5Field('Answer', config_name='default')

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question
    
class ContactSection(models.Model):
    resume = models.ForeignKey(
        'Resume',
        related_name='contact_sections',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=100, default="Contact")
    subtitle = CKEditor5Field('Sub title', config_name='default')
    description = CKEditor5Field('Left Pannel Description', config_name='default')

    location = models.TextField()
    phone_numbers = models.TextField(
        help_text="One per line"
    )
    email_addresses = models.TextField(
        help_text="One per line"
    )

    receive_email_at = models.EmailField(
        help_text="Where contact form emails are sent"
    )

    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    section = models.ForeignKey(
        ContactSection,
        related_name='messages',
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = CKEditor5Field('Message', config_name='default')

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        # Lazy import prevents circular imports
        # validate_resume_content(self)
        
    def __str__(self):
        return f"{self.name} – {self.subject}"