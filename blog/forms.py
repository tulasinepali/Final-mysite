from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    # Honeypot field: invisible to real users, bots usually fill it in
    hp_website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'autocomplete': 'off', 'tabindex': '-1'})
    )

    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'Your Full Name *',
                'required': True,
                'maxlength': '120',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'Your Email Address (strictly private) *',
                'required': True,
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control rounded-3',
                'rows': 4,
                'placeholder': 'Write your thoughts, questions, or feedback here...',
                'required': True,
                'maxlength': '1200',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Please provide a valid name (at least 2 characters).")
        return name

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 5:
            raise forms.ValidationError("Comment message is too short (at least 5 characters).")
        return content
