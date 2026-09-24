import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def send_web_push_notification(title, message, url=None, image_url=None):
    """
    Broadcasts a web push notification to all subscribed visitors via OneSignal REST API.
    Only dispatches if `enable_web_push` is ON and both `onesignal_app_id` and
    `onesignal_rest_api_key` are configured in Site Settings.
    """
    from core.models import SiteSettings
    try:
        site_settings = SiteSettings.objects.first()
        if not site_settings:
            return False, "SiteSettings not found"

        if not site_settings.enable_web_push:
            return False, "Web push is disabled in Site Settings"

        app_id = (site_settings.onesignal_app_id or "").strip()
        api_key = (site_settings.onesignal_rest_api_key or "").strip()

        if not app_id or not api_key:
            return False, "OneSignal App ID or REST API Key is missing in Site Settings"

        payload = {
            "app_id": app_id,
            "included_segments": ["Total Subscriptions"],
            "headings": {"en": title},
            "contents": {"en": message},
        }

        if url:
            payload["url"] = url

        if image_url:
            payload["big_picture"] = image_url
            payload["chrome_web_image"] = image_url

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://onesignal.com/api/v1/notifications",
            data=data,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Basic {api_key}",
                "User-Agent": "TulasiNepali-LearningPlatform/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            logger.info("OneSignal push notification sent: %s", resp_data)
            return True, resp_data

    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        logger.warning("OneSignal HTTPError %s: %s", e.code, err_msg)
        return False, f"HTTP {e.code}: {err_msg}"
    except Exception as e:
        logger.error("Failed to send push notification: %s", str(e))
        return False, str(e)
