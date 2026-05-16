class TemplateService:
    
    @staticmethod
    def otp_message(otp):

        return f"""
Your Resume Builder OTP is:

{otp}

Valid for 10 minutes.
"""