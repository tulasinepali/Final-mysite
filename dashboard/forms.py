import os
import uuid
from django import forms
from django.utils.text import slugify
from django_ckeditor_5.widgets import CKEditor5Widget
from core.models import SiteSettings, Category, Tag, AdPlacement
from notes.models import Note
from blog.models import BlogPost
from downloads.models import Download
from quiz.models import Quiz, Question
from tools.models import Tool, Widget, WidgetSetting, PatroEvent


def auto_generate_slug(model_class, title, slug_val, instance_pk=None, prefix='item'):
    slug_val = (slug_val or '').strip()
    if not slug_val and title:
        base_slug = slugify(title)
        if not base_slug:
            base_slug = f"{prefix}-{uuid.uuid4().hex[:8]}"
        slug_val = base_slug
        counter = 1
        while model_class.objects.filter(slug=slug_val).exclude(pk=instance_pk).exists():
            slug_val = f"{base_slug}-{counter}"
            counter += 1
    return slug_val


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
        self.fields['slug'].required = False
        # Make auto-managed fields not required
        self.fields['views'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['featured_image'].required = False
        self.fields['tags'].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        instance_pk = self.instance.pk if self.instance else None
        return auto_generate_slug(Note, title, slug, instance_pk=instance_pk, prefix='note')


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
        self.fields['slug'].required = False
        self.fields['views'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['featured_image'].required = False
        self.fields['tags'].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        instance_pk = self.instance.pk if self.instance else None
        return auto_generate_slug(BlogPost, title, slug, instance_pk=instance_pk, prefix='blog')


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
        self.fields['slug'].required = False
        self.fields['file_type'].required = False
        self.fields['download_count'].required = False
        self.fields['file_size'].required = False
        self.fields['thumbnail'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['tags'].required = False

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        instance_pk = self.instance.pk if self.instance else None
        return auto_generate_slug(Download, title, slug, instance_pk=instance_pk, prefix='download')

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        file_type = cleaned_data.get('file_type')
        if file and not file_type:
            fname = getattr(file, 'name', '') or ''
            ext = os.path.splitext(fname)[1].lower().lstrip('.')
            if ext == 'pdf':
                cleaned_data['file_type'] = 'pdf'
            elif ext in ['doc', 'docx']:
                cleaned_data['file_type'] = 'docx'
            elif ext in ['ppt', 'pptx']:
                cleaned_data['file_type'] = 'ppt'
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
                cleaned_data['file_type'] = 'zip'
            else:
                cleaned_data['file_type'] = 'other'
        return cleaned_data


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
        self.fields['slug'].required = False
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

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        instance_pk = self.instance.pk if self.instance else None
        return auto_generate_slug(Quiz, title, slug, instance_pk=instance_pk, prefix='quiz')

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


class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ['name', 'slug', 'category', 'icon', 'order', 'is_active', 'short_description', 'meta_title', 'meta_description']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-calculator, bi-calendar3'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'name'})
        self.fields['slug'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False


class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = ['title', 'slug', 'tool', 'icon', 'badge_text', 'default_width', 'default_height', 'order', 'is_active', 'short_description', 'custom_html']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'custom_html': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '<iframe ...></iframe>'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'tool': forms.Select(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_text': forms.TextInput(attrs={'class': 'form-control'}),
            'default_width': forms.TextInput(attrs={'class': 'form-control'}),
            'default_height': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        self.fields['slug'].required = False
        self.fields['tool'].required = False
        self.fields['custom_html'].required = False


class WidgetSettingForm(forms.ModelForm):
    class Meta:
        model = WidgetSetting
        fields = ['allow_embedding', 'branding_text', 'branding_url', 'show_ads_in_widgets']
        widgets = {
            'branding_text': forms.TextInput(attrs={'class': 'form-control'}),
            'branding_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class PatroEventForm(forms.ModelForm):
    class Meta:
        model = PatroEvent
        fields = ['year_bs', 'month_bs', 'day_bs', 'title', 'title_en', 'is_public_holiday', 'event_type', 'description']
        widgets = {
            'year_bs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2083 or 2084'}),
            'month_bs': forms.Select(attrs={'class': 'form-control'}),
            'day_bs': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 32}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. नयाँ वर्ष, विजया दशमी'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New Year, Vijaya Dashami'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Optional notes or gazette notice reference'}),
        }


class PatroEventImportForm(forms.Form):
    target_year = forms.IntegerField(
        initial=2084,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2084'}),
        help_text="Target Bikram Sambat year for the imported events"
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.json'}),
        help_text="Upload a .CSV or .JSON file containing holidays and events"
    )
    replace_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Overwrite/replace any existing events for this year"
    )



