from apps.social.models.social_login_models import SocialLoginSetting

print("SOCIAL PIPELINE FILE LOADED")


def load_social_settings(
    strategy,
    backend,
    *args,
    **kwargs
):

    provider = backend.name

    social = SocialLoginSetting.objects.filter(
        provider=provider,
        is_active=True
    ).first()

    print("BACKEND:", provider)

    if social:

        backend.KEY = social.client_id
        backend.SECRET = social.client_secret

        print("KEY LOADED")
        print("SECRET LOADED")

    else:

        print("NO SOCIAL CONFIG FOUND")