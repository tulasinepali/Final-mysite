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
            'negative_marking_value': forms.NumberInput(attrs={'step': '0.25', 'min': '0', 'max': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(module='quiz')
        self.fields['slug'].widget.attrs.update({'data-slug-from': 'title'})
        self.fields['attempts'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False
        self.fields['description'].required = False
        self.fields['negative_marking_value'].required = False


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


class AdPlacementForm(forms.ModelForm):
    class Meta:
        model = AdPlacement
        fields = '__all__'
        widgets = {
            'ad_code': forms.Textarea(attrs={'rows': 5}),
        }
