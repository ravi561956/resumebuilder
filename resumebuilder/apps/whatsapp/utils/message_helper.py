import re
from bs4 import BeautifulSoup
from apps.whatsapp.models.whatsapp_msg import WhatsappMessage

def html_to_whatsapp(text):
    
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")

    # bold
    for tag in soup.find_all(["strong", "b"]):

        tag.string = f"*{tag.get_text()}*"

    # italic
    for tag in soup.find_all(["em", "i"]):

        tag.string = f"_{tag.get_text()}_"

    # strike
    for tag in soup.find_all(["del", "strike"]):

        tag.string = f"~{tag.get_text()}~"

    # convert line breaks
    for br in soup.find_all("br"):

        br.replace_with("\n")

    text = soup.get_text("\n")

    text = re.sub(r'\n+', '\n', text)

    text = text.replace("&nbsp;", " ")

    return text.strip()

def get_whatsapp_message(
    message_type,
    replacements=None
):

    try:

        template = WhatsappMessage.objects.get(
            message_type=message_type,
            is_active=True
        )

    except WhatsappMessage.DoesNotExist:

        return None

    # default message
    message = ""

    # welcome message
    if message_type == "welcome":

        username = ""

        if replacements:
            username = replacements.get(
                "username",
                ""
            )

        message = f"""
{template.title}

Hi {username},

{template.body}
"""

    # otp message
    elif message_type == "otp":
        username = ""
        otp = " "
        otp = replacements.get(
            "otp",
            ""
        )
        username = replacements.get(
            "username",
            ""
        )
        message = f"""
            {template.title}
            
            Hi {username},
            
            {template.body} {otp}
            """

    # confirmation message
    elif message_type == "confirmation":
        
        username = ""
        resume_url = ""

        if replacements:

            username = replacements.get(
                "username",
                ""
            )

            resume_url = replacements.get(
                "resume_url",
                ""
            )

            message = f"""
        ✅ {template.title}

        Hi {username},

        Your account has been verified successfully.
        
        🌐 Your Resume Website:
        {resume_url}
        
        {template.body}
        """

    # dynamic replacements
    if replacements:

        for key, value in replacements.items():

            message = message.replace(
                "{" + key + "}",
                str(value)
            )

    # convert html to whatsapp text
    return html_to_whatsapp(message)