from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from core.models import SiteSettings, Category, Tag, AdPlacement
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz, Question


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'site_description': CKEditor5Widget(config_name='default'),
            'owner_bio': CKEditor5Widget(config_name='default'),
            'mission': CKEditor5Widget(config_name='default'),
            'vision': CKEditor5Widget(config_name='default'),
            'address': forms.Textarea(attrs={'rows': 2}),
            'email_host_password': forms.PasswordInput(render_value=True, attrs={'placeholder': '••••••••••••••••'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(config_name='default'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'name'})


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = '__all__'


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = '__all__'
        widgets = {
            'content': CKEditor5Widget(config_name='notes_toolbar'),
            'summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(module='notes')
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        # Make auto-managed fields not required
        self.fields['views'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['featured_image'].required = False
        self.fields['tags'].required = False


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = '__all__'
        widgets = {
            'content': CKEditor5Widget(config_name='blog_toolbar'),
            'summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(module='blog')
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        self.fields['views'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['featured_image'].required = False
        self.fields['tags'].required = False


class DownloadForm(forms.ModelForm):
    class Meta:
        model = Download
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(config_name='default'),
            'summary': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(module='downloads')
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        self.fields['download_count'].required = False
        self.fields['file_size'].required = False
        self.fields['thumbnail'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['tags'].required = False


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(config_name='default'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(module='quiz')
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        self.fields['attempts'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['description'].required = False
        # Negative marking fields — only present after migration is applied
        if 'negative_marking_value' in self.fields:
            self.fields['negative_marking_value'].required = False
            self.fields['negative_marking_value'].widget = forms.NumberInput(attrs={'step': '1', 'min': '0', 'max': '100'})
            # Set initial value to 20 if creating a new quiz (no instance)
            if not self.instance or not self.instance.pk:
                self.fields['negative_marking_value'].initial = 20

    def clean_negative_marking_value(self):
        """Ensure negative_marking_value is never None or 0 when negative marking is enabled."""
        value = self.cleaned_data.get('negative_marking_value')
        if value is None or value == '':
            return 20
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 20
        if value <= 0:
            return 20
        return value


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        exclude = ['quiz']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter the question text...'}),
            'explanation': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional explanation shown after answering...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['explanation'].required = False


class QuestionImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Select Excel File (.xlsx)',
        help_text='Upload an .xlsx file with columns: question_text, option_a, option_b, option_c, option_d, correct_answer, explanation (optional), order (optional)',
        widget=forms.ClearableFileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control-file',
        })
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if not file:
            raise forms.ValidationError('Please select a file.')
        # Check file extension
        if not file.name.endswith(('.xlsx', '.xls')):
            raise forms.ValidationError('Only .xlsx and .xls files are supported. Please upload an Excel file.')
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise forms.ValidationError('File size must be under 5MB.')
        return file


class AdPlacementForm(forms.ModelForm):
    class Meta:
        model = AdPlacement
        fields = '__all__'
        widgets = {
            'ad_code': forms.Textarea(attrs={'rows': 5}),
            'link_url': forms.URLInput(attrs={'placeholder': 'https://example.com (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ad_code'].required = False
        self.fields['ad_image'].required = False
        self.fields['link_url'].required = False


class BroadcastEmailForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 🚀 New Computer Operator & Tech Practice Quiz is Live!'
        }),
        help_text='The subject line of the email displayed in subscribers\' inboxes.'
    )
    headline = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Test Your Knowledge with Our Latest Practice Exam'
        }),
        help_text='Main banner title inside the email template.'
    )
    body_content = forms.CharField(
        required=True,
        widget=CKEditor5Widget(config_name='default'),
        help_text='The main message or announcement for your subscribers.'
    )
    cta_text = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Start Free MCQ Quiz Now'
        }),
        help_text='Action button label (optional).'
    )
    cta_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://tulasinepali.com.np/quiz/...'
        }),
        help_text='Destination link when subscribers click the action button.'
    )
    send_test_only = forms.BooleanField(
        required=False,
        initial=False,
        label="Send Test Email Only",
        help_text="Send this announcement only to the test email address below to inspect before blasting to everyone."
    )
    test_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your-email@gmail.com'
        }),
        help_text="Target email address for the test preview."
    )

    def clean(self):
        cleaned_data = super().clean()
        send_test = cleaned_data.get('send_test_only')
        test_email = cleaned_data.get('test_email')
        if send_test and not test_email:
            self.add_error('test_email', 'Please provide a test recipient email address when test mode is selected.')
        return cleaned_data

