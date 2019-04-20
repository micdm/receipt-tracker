from typing import Dict

from django.conf import settings


def add_common_context(context: Dict) -> Dict:
    context.update({
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID if not settings.DEBUG else None
    })
    return context
