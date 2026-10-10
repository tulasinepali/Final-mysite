from django.core.management.base import BaseCommand
from core.models import SiteSettings, AITopicQueue
from core.ai_blogger import generate_content_for_topic, run_daily_ai_generation_job


class Command(BaseCommand):
    help = "Generate daily scheduled blog post and/or study note using Google Gemini AI"

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'blog', 'note'],
            default='all',
            help='Content type to process (default: all enabled types)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run even if daily schedule toggle is disabled in Site Settings'
        )
        parser.add_argument(
            '--topic',
            type=str,
            default='',
            help='Run immediately for an ad-hoc topic string'
        )

    def handle(self, *args, **options):
        c_type = options.get('type')
        force = options.get('force')
        custom_topic = options.get('topic')

        self.stdout.write(self.style.NOTICE("Starting AI Content Generation process..."))

        if custom_topic:
            topic_type = 'blog' if c_type in ['all', 'blog'] else 'note'
            self.stdout.write(f"Generating on-demand {topic_type} for topic: {custom_topic}")
            topic_obj = AITopicQueue.objects.create(
                title=custom_topic,
                content_type=topic_type,
                status='pending'
            )
            ok, res, log = generate_content_for_topic(topic_obj)
            if ok:
                self.stdout.write(self.style.SUCCESS(f"Successfully generated {topic_type}: {res.title}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to generate: {res}"))
            return

        settings = SiteSettings.objects.first()
        if not settings:
            self.stdout.write(self.style.ERROR("No SiteSettings found in database."))
            return

        if not force and not settings.enable_daily_ai_blog and not settings.enable_daily_ai_note:
            self.stdout.write(self.style.WARNING("Both Daily AI Blog and Note generation are disabled in Site Settings."))
            self.stdout.write(self.style.NOTICE("Enable them in your dashboard or run with --force."))
            return

        # 1. Process Blog
        if c_type in ['all', 'blog'] and (force or settings.enable_daily_ai_blog):
            blog_topic = AITopicQueue.objects.filter(content_type='blog', status='pending').first()
            if blog_topic:
                self.stdout.write(f"Processing queued blog topic: {blog_topic.title}")
                ok, res, log = generate_content_for_topic(blog_topic)
                if ok:
                    self.stdout.write(self.style.SUCCESS(f"Blog post generated: {res.title}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Blog generation error: {res}"))
            else:
                self.stdout.write(self.style.WARNING("No pending blog topics found in queue."))

        # 2. Process Note
        if c_type in ['all', 'note'] and (force or settings.enable_daily_ai_note):
            note_topic = AITopicQueue.objects.filter(content_type='note', status='pending').first()
            if note_topic:
                self.stdout.write(f"Processing queued study note topic: {note_topic.title}")
                ok, res, log = generate_content_for_topic(note_topic)
                if ok:
                    self.stdout.write(self.style.SUCCESS(f"Study note generated: {res.title}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Note generation error: {res}"))
            else:
                self.stdout.write(self.style.WARNING("No pending note topics found in queue."))

        self.stdout.write(self.style.SUCCESS("AI Generation Job Finished."))
