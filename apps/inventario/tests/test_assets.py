import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.template import Context, Template
from django.test import SimpleTestCase, override_settings


class AssetCacheTests(SimpleTestCase):
    def test_stylesheet_url_changes_when_source_changes(self):
        with TemporaryDirectory() as temporary, override_settings(BASE_DIR=Path(temporary)):
            source = Path(temporary) / "static" / "css" / "app.css"
            source.parent.mkdir(parents=True)
            source.write_text("body { color: black; }", encoding="utf-8")
            markup = Template("{% load assets %}{% versioned_static 'css/app.css' %}")
            first = markup.render(Context())
            source_stat = source.stat()
            os.utime(source, ns=(source_stat.st_atime_ns, source_stat.st_mtime_ns + 1_000_000_000))
            updated = markup.render(Context())
            self.assertTrue(first.startswith("/static/css/app.css?v="))
            self.assertNotEqual(first, updated)

