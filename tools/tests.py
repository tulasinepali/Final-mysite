import json
from django.test import TestCase, Client
from django.urls import reverse
from tools.models import Tool, Widget, WidgetSetting

class ToolsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.tool_date = Tool.objects.get(slug='date-converter')
        self.tool_age = Tool.objects.get(slug='age-calculator')
        self.widget_age = Widget.objects.get(slug='age-calculator')

    def test_tools_index_view(self):
        response = self.client.get(reverse('tools:tools_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nepali Date Converter")
        self.assertContains(response, "Universal Age Calculator")

    def test_date_converter_view(self):
        response = self.client.get(reverse('tools:date_converter'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nepali Date Converter")

    def test_age_calculator_view(self):
        response = self.client.get(reverse('tools:age_calculator'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Universal Age Calculator")
        
        # Verify tool model & tool template specific content has NO mention of Loksewa
        tool = response.context.get('tool')
        if tool:
            self.assertNotIn("loksewa", (tool.name + " " + tool.short_description + " " + tool.meta_title + " " + tool.meta_description).lower())
            self.assertNotIn("लोकसेवा", (tool.name + " " + tool.short_description + " " + tool.meta_title + " " + tool.meta_description))

        # Check content inside main block
        html = response.content.decode('utf-8')
        main_content = html[html.find('<main'):html.find('</main>')] if '<main' in html else html
        main_lower = main_content.lower()
        self.assertNotIn("loksewa", main_lower)
        self.assertNotIn("lok sewa", main_lower)
        self.assertNotIn("लोकसेवा", main_lower)

    def test_unicode_converter_view(self):
        response = self.client.get(reverse('tools:unicode_converter'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preeti")

    def test_widgets_index_view(self):
        response = self.client.get(reverse('tools:widgets_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Free Embeddable Widgets")

    def test_widget_embed_view(self):
        response = self.client.get(reverse('tools:widget_embed', kwargs={'slug': 'age-calculator'}))
        self.assertEqual(response.status_code, 200)
        # Should NOT have X-Frame-Options: DENY or SAMEORIGIN due to xframe_options_exempt
        self.assertNotEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertNotEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_api_track_embed(self):
        initial_count = self.widget_age.embed_count
        response = self.client.post(
            reverse('tools:api_track_embed', kwargs={'slug': 'age-calculator'}),
            data=json.dumps({'referrer': 'https://schoolportal.edu.np/calendar/'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.widget_age.refresh_from_db()
        self.assertEqual(self.widget_age.embed_count, initial_count + 1)

        from tools.models import WidgetUsage
        usage = WidgetUsage.objects.filter(widget=self.widget_age, domain='schoolportal.edu.np').first()
        self.assertIsNotNone(usage)
        self.assertFalse(usage.is_internal)
        self.assertEqual(usage.total_views, 1)


    def test_nepali_patro_view(self):
        response = self.client.get(reverse('tools:nepali_patro'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "नेपाली पात्रो २०८३")

    def test_nepali_patro_widget_embed(self):
        response = self.client.get(reverse('tools:widget_embed', kwargs={'slug': 'nepali-patro'}))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.headers.get('X-Frame-Options'), 'DENY')

    def test_api_patro_events(self):
        response = self.client.get(reverse('tools:api_patro_events') + '?year=2083')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('2083-01-01', data)
        self.assertTrue(data['2083-01-01']['is_holiday'])


