from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe',
            'id': 'id_name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'john@example.com',
            'id': 'id_email',
        })
    )
    subject = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'How can we help?',
            'id': 'id_subject',
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Type your message here...',
            'rows': 6,
            'id': 'id_message',
        })
    )
