from django import forms
import re


class URLForm(forms.Form):
    """Form for malicious URL detection input."""
    url = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'https://example.com/suspicious/path?param=value',
            'id': 'url-input',
            'autocomplete': 'off',
            'spellcheck': 'false',
        }),
        label='URL to Analyze',
        max_length=2048,
        min_length=4,
        error_messages={
            'required': 'Please enter a URL to analyze.',
            'min_length': 'URL must be at least 4 characters.',
        }
    )

    def clean_url(self):
        url = self.cleaned_data['url'].strip()
        # Add scheme if missing for feature extraction to work
        if not re.match(r'^https?://', url, re.IGNORECASE):
            if not url.startswith('//'):
                url = 'http://' + url
        return url
