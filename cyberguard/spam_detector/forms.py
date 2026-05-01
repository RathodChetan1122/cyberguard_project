from django import forms


class SMSForm(forms.Form):
    """Form for SMS spam detection input."""
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Paste your SMS message here...\n\nExample: "Congratulations! You have won a £1000 prize. Call now to claim!"',
            'id': 'sms-input',
            'maxlength': 5000,
        }),
        label='SMS Message',
        max_length=5000,
        min_length=3,
        error_messages={
            'required': 'Please enter an SMS message to analyze.',
            'min_length': 'Message must be at least 3 characters.',
        }
    )
