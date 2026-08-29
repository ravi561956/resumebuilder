from .models import ModerationSetting


def get_moderation_settings():
    settings_obj = ModerationSetting.objects.first()
    
    if not settings_obj:
        
        settings_obj = ModerationSetting.objects.create(
            moderation_enabled=True,
            keyword_filter_enabled=True
        )
        print(settings_obj)
    return settings_obj


def get_bad_keywords():
  
    settings_obj = get_moderation_settings()
    print('bad keyword', settings_obj)
    return [
        keyword.strip().lower()
        for keyword in settings_obj.bad_keywords.splitlines()
        if keyword.strip()
    ]