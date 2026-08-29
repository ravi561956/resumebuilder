from django.contrib import admin
from .models import Resume, ResumeStat, ResumeSocial, ResumeFloatingCard, ResumeSkill, ResumeJourney, SkillCategory, Skill, Profession, Certification, Journey, Excellence, ServiceSection, Service, PortfolioSection, PortfolioCategory, PortfolioItem, TestimonialSection, Testimonial, ReviewPlatform, FAQSection, FAQ, ContactSection, ContactMessage
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError

class UserRestrictedAdmin(admin.ModelAdmin):
    """
    Admin base class for resume-owned content.

    Superusers can manage everything. Normal users can only see/create/update/delete
    objects that belong to their own Resume. Resume selectors are hidden for normal
    users and the owner Resume is assigned automatically on creation.
    """

    class Media:
        js = ('ai_content/admin_ai.js',)

    OWNER_LOOKUPS = {
        'resumestat': 'resume__user',
        'resumesocial': 'resume__user',
        'resumefloatingcard': 'resume__user',
        'resumeskill': 'resume__user',
        'resumejourney': 'resume__user',
        'skillcategory': 'resume__user',
        'skill': 'category__resume__user',
        'profession': 'resume__user',
        'certification': 'certificate__resume__user',
        'journey': 'resume__user',
        'excellence': 'journey__resume__user',
        'servicesection': 'resume__user',
        'service': 'section__resume__user',
        'portfoliosection': 'resume__user',
        'portfoliocategory': 'section__resume__user',
        'portfolioitem': 'section__resume__user',
        'testimonialsection': 'resume__user',
        'testimonial': 'section__resume__user',
        'reviewplatform': 'section__resume__user',
        'faqsection': 'resume__user',
        'faq': 'section__resume__user',
        'contactsection': 'resume__user',
        'contactmessage': 'section__resume__user',
    }

    # Any FK with one of these names points to an ownership chain above.
    # The related queryset is restricted automatically for normal users.

    def _owner_lookup(self, model=None):
        model = model or self.model
        return self.OWNER_LOOKUPS.get(model._meta.model_name)

    def _owned_queryset(self, model, user):
        manager = model._default_manager.all()
        lookup = self._owner_lookup(model)
        if lookup:
            return manager.filter(**{lookup: user})
        if model is Resume:
            return manager.filter(user=user)
        return manager.none()

    def _default_resume(self, user):
        return (
            Resume.objects.filter(user=user, is_active=True).order_by('id').first()
            or Resume.objects.filter(user=user).order_by('id').first()
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        lookup = self._owner_lookup()
        return qs.filter(**{lookup: request.user}) if lookup else qs.none()

    def _belongs_to_user(self, obj, user):
        lookup = self._owner_lookup()
        if not lookup:
            return False
        value = obj
        for part in lookup.split('__')[:-1]:
            value = getattr(value, part, None)
            if value is None:
                return False
        return value == user

    def get_form(self, request, obj=None, **kwargs):
        """Hide Resume from normal users; it is assigned from request.user."""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and 'resume' in form.base_fields:
            form.base_fields.pop('resume')
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            related_model = db_field.remote_field.model
            if related_model is Resume:
                kwargs['queryset'] = Resume.objects.filter(user=request.user)
            else:
                lookup = self._owner_lookup(related_model)
                if lookup:
                    kwargs['queryset'] = related_model._default_manager.filter(
                        **{lookup: request.user}
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            related_model = db_field.remote_field.model
            if related_model is Resume:
                kwargs['queryset'] = Resume.objects.filter(user=request.user)
            else:
                lookup = self._owner_lookup(related_model)
                if lookup:
                    kwargs['queryset'] = related_model._default_manager.filter(
                        **{lookup: request.user}
                    )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            # Root Resume relation: always bind a new object to the logged-in user's
            # active Resume. Never trust a client-supplied owner relationship.
            if hasattr(obj, 'resume_id'):
                owner_resume = self._default_resume(request.user)
                if owner_resume is None:
                    raise ValidationError(
                        'You must create a Resume before creating resume content.'
                    )
                if change:
                    current_resume = getattr(obj, 'resume', None)
                    if current_resume is None or current_resume.user_id != request.user.id:
                        raise ValidationError('You can only modify content belonging to your own Resume.')
                else:
                    obj.resume = owner_resume

            # For nested models, validate the resolved ownership chain.
            elif not self._belongs_to_user(obj, request.user):
                raise ValidationError('You can only save content belonging to your own Resume.')

        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return self._belongs_to_user(obj, request.user)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return self._belongs_to_user(obj, request.user)

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1

class ExcellenceInline(admin.TabularInline):
    model= Excellence
    extra = 1

class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1

class ResumeJourneyInline(admin.TabularInline):
    model = ResumeJourney
    extra = 1
    fields = ('year', 'description', 'order', 'is_active')

class ResumeSkillInline(admin.TabularInline):
    model = ResumeSkill
    extra = 1
    fields = (
        'title',
        'icon_class',
        'description',
        'aos_animation',
        'aos_delay',
        'order',
        'is_active'
    )

class ResumeFloatingCardInline(admin.TabularInline):
    model = ResumeFloatingCard
    extra = 1
    fields = (
        'title',
        'icon_class',
        'card_class',
        'aos_animation',
        'aos_delay',
        'order',
        'is_active'
    )

class ResumeSocialInline(admin.TabularInline):
    model = ResumeSocial
    extra = 1
    fields = ('platform', 'url', 'icon_class', 'order', 'is_active')
    ordering = ('order',)

class ResumeStatInline(admin.TabularInline):
    model = ResumeStat
    extra = 1
    fields = ('icon_class', 'value', 'label', 'aos_delay', 'order')
    ordering = ('order',)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    change_form_template = 'admin/resume/resume/change_form.html'

    class Media:
        js = ('ai_content/admin_ai.js',)

    list_display = ('name', 'title', 'theme', 'pdf_template', 'preview_pdf', 'is_active', 'updated_at')
    list_filter = ('theme', 'pdf_template', 'is_active')

    fieldsets = (
        ('Basic Info', {'fields': ('subdomain', 'name', 'title', 'position', 'email', 'phone', 'address', 'website', 'tags', 'tag_line', 'short_desc')}),
        ('Images', {'fields': ('profile_image', 'banner_image')}),
        ('Resume Details', {'fields': ('summary', 'skills')}),

        # ✅ FIX HERE
        ('Design Settings', {'fields': ('theme', 'pdf_template')}),

        ('Status', {'fields': ('is_active',)}),
    )
    
    def preview_pdf(self, obj):
            return format_html(
            '<a href="{}" target="_blank">Preview PDF</a>',
            reverse('resume_pdf_preview', args=[obj.id])
        )

    preview_pdf.short_description = "Preview"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ✅ Superuser sees all
        if request.user.is_superuser:
            return qs
        # ✅ Normal user sees only own resume
        return qs.filter(user=request.user)
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return True

        return obj.user == request.user  
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if obj is None:
            return True

        return obj.user == request.user
    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.full_clean()
        super().save_model(request, obj, form, change)

@admin.register(SkillCategory)
class SkillCategoryAdmin(UserRestrictedAdmin):
    list_display = ('title', 'resume', 'order')
    inlines = [SkillInline]

@admin.register(Profession)
class ProfessionAdmin(UserRestrictedAdmin):
    inlines = [CertificationInline]
    filter_horizontal = ('resume_stats',)

@admin.register(Journey)
class JourneyAdmin(UserRestrictedAdmin):
    inlines = [ExcellenceInline]

@admin.register(ServiceSection)
class ServiceSectionAdmin(UserRestrictedAdmin):
    inlines = [ServiceInline]

class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 1
    fields = (
        'title',
        'image',
        'order',
        'is_active'
    )
    ordering = ('order',)
    show_change_link = True


class PortfolioCategoryInline(admin.TabularInline):
    model = PortfolioCategory
    extra = 1
    fields = ('title', 'slug', 'order')
    ordering = ('order',)


@admin.register(PortfolioSection)
class PortfolioSectionAdmin(UserRestrictedAdmin):
    list_display = ('title', 'resume', 'is_active')
    inlines = [PortfolioCategoryInline, PortfolioItemInline]


@admin.register(PortfolioItem)
class PortfolioItemAdmin(UserRestrictedAdmin):
    list_display = ('title', 'section', 'order', 'is_active')
    list_filter = ('section', 'is_active', 'categories')
    filter_horizontal = ('categories',)
    ordering = ('section', 'order')


class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 1
    fields = (
        'author_name',
        'author_role',
        'source',
        'rating',
        'order',
        'is_active'
    )
    ordering = ('order',)
    show_change_link = True


class ReviewPlatformInline(admin.TabularInline):
    model = ReviewPlatform
    extra = 1


@admin.register(TestimonialSection)
class TestimonialSectionAdmin(UserRestrictedAdmin):
    list_display = (
        'title',
        'average_rating',
        'total_reviews',
        'is_active'
    )
    inlines = [TestimonialInline, ReviewPlatformInline]


@admin.register(Testimonial)
class TestimonialAdmin(UserRestrictedAdmin):
    list_display = (
        'author_name',
        'source',
        'rating',
        'section',
        'order',
        'is_active'
    )
    list_filter = ('section', 'rating', 'is_active')
    ordering = ('section', 'order')

class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1
    fields = (
        'question',
        'order',
        'is_active'
    )
    ordering = ('order',)
    show_change_link = True


@admin.register(FAQSection)
class FAQSectionAdmin(UserRestrictedAdmin):
    list_display = (
        'title',
        'resume',
        'order',
        'is_active'
    )
    list_filter = ('is_active', 'resume')
    ordering = ('order',)
    inlines = [FAQInline]


@admin.register(FAQ)
class FAQAdmin(UserRestrictedAdmin):
    list_display = (
        'question',
        'section',
        'order',
        'is_active'
    )
    list_filter = ('section', 'is_active')
    ordering = ('section', 'order')

@admin.register(ContactSection)
class ContactSectionAdmin(UserRestrictedAdmin):
    list_display = ('title', 'resume', 'receive_email_at', 'is_active')
    list_filter = ('is_active', 'resume')


@admin.register(ContactMessage)
class ContactMessageAdmin(UserRestrictedAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')