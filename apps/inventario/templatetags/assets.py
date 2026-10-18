from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    """Invalidate cached local assets whenever their source file changes."""
    url = static(path)
    source = settings.BASE_DIR / "static" / path
    try:
        version = source.stat().st_mtime_ns
    except OSError:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"

