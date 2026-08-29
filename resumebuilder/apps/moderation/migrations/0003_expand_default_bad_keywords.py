from django.db import migrations, models

OLD_DEFAULT = (
    "escort\n"
    "porn\n"
    "call girl\n"
    "sex service\n"
    "adult service"
)

NEW_DEFAULT = (
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
)


def expand_bad_keywords(apps, schema_editor):
    """
    Only touch rows that still hold the original out-of-the-box default.
    Any list an admin has already edited by hand is left alone.
    """
    ModerationSetting = apps.get_model("moderation", "ModerationSetting")

    ModerationSetting.objects.filter(
        bad_keywords__in=[OLD_DEFAULT, OLD_DEFAULT.replace("\n", "\r\n")]
    ).update(bad_keywords=NEW_DEFAULT)


def revert_bad_keywords(apps, schema_editor):
    ModerationSetting = apps.get_model("moderation", "ModerationSetting")

    ModerationSetting.objects.filter(bad_keywords=NEW_DEFAULT).update(
        bad_keywords=OLD_DEFAULT
    )


class Migration(migrations.Migration):

    dependencies = [
        ("moderation", "0002_moderationviolation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="moderationsetting",
            name="bad_keywords",
            field=models.TextField(
                blank=True,
                default=NEW_DEFAULT,
                help_text=(
                    "One keyword per line. Deliberately excludes sexual-orientation "
                    "or gender-identity words (e.g. 'gay', 'lesbian') since those are "
                    "legitimate identity terms, not indicators of explicit content \u2014 "
                    "blocking them would wrongly flag genuine resumes/bios."
                ),
            ),
        ),
        migrations.RunPython(expand_bad_keywords, revert_bad_keywords),
    ]
