from django import forms


class CoverLetterForm(forms.Form):
    job_title = forms.CharField(max_length=200, required=True)
    company_name = forms.CharField(max_length=200, required=False)
    job_description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 10, 'placeholder': 'Paste the job description here...'}),
    )
    additional_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Optional: tone, achievements to emphasize, etc.'}),
    )
