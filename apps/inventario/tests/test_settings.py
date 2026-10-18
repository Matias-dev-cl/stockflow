import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class RuntimeSettingsTests(SimpleTestCase):
    def load_settings(self):
        return runpy.run_path(str(Path(settings.BASE_DIR) / "config" / "settings.py"))

    def test_dotenv_is_loaded_from_project_directory(self):
        with patch("dotenv.load_dotenv") as loader, patch.dict(os.environ, {"DEBUG": "1"}):
            self.load_settings()
        loader.assert_called_once_with(Path(settings.BASE_DIR) / ".env")

    def test_postgresql_url_decodes_credentials(self):
        environment = {
            "DEBUG": "1",
            "DATABASE_URL": "postgresql://user%40company:pass%3Aword@localhost:5432/stockflow",
        }
        with patch("dotenv.load_dotenv"), patch.dict(os.environ, environment):
            result = self.load_settings()
        database = result["DATABASES"]["default"]
        self.assertEqual(database["USER"], "user@company")
        self.assertEqual(database["PASSWORD"], "pass:word")

    def test_production_rejects_shared_development_secret(self):
        with patch("dotenv.load_dotenv"), patch.dict(
            os.environ, {"DEBUG": "0", "SECRET_KEY": "local-only-change-before-deploy"}
        ):
            with self.assertRaises(ImproperlyConfigured):
                self.load_settings()

    def test_invalid_database_url_does_not_silently_use_sqlite(self):
        for url in ("invalid://database", "postgres-wrong://localhost/stockflow"):
            with self.subTest(url=url), patch("dotenv.load_dotenv"), patch.dict(
                os.environ, {"DEBUG": "1", "DATABASE_URL": url}
            ):
                with self.assertRaises(ImproperlyConfigured):
                    self.load_settings()

