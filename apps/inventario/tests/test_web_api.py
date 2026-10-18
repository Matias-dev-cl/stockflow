from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.inventario.models import Category, Location, Movement, Product, StockBalance
from apps.inventario.services import record_movement


class WebAndAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.operator = User.objects.create_user("operador", password="local-password-123")
        cls.admin = User.objects.create_user("admin", password="local-password-123", is_staff=True)
        cls.category = Category.objects.create(name="Oficina")
        cls.product = Product.objects.create(sku="P-1", name="Producto", minimum=5, category=cls.category)
        cls.location = Location.objects.create(code="B1", name="Bodega")
        record_movement(product=cls.product, location=cls.location, kind="IN",
                        quantity=10, reason="Inicial", user=cls.operator)

    def payload(self, **overrides):
        payload = {"product": self.product.pk, "location": self.location.pk,
                   "kind": "OUT", "quantity": 2, "reason": "Entrega"}
        payload.update(overrides)
        return payload

    def test_anonymous_users_cannot_read_inventory(self):
        self.assertRedirects(self.client.get(reverse("products")), "/accounts/login/?next=/productos/")
        api = APIClient()
        self.assertIn(api.get(reverse("api-products")).status_code, [401, 403])

    def test_operator_cannot_create_or_quick_edit_product(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("product_detail", args=[self.product.pk]),
                                    {"action": "quick_edit", "name": "Alterado", "minimum": 1})
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Producto")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(reverse("product_create"), {"sku": "BAD"}).status_code, 403)

    def test_admin_can_quick_edit_without_changing_stock(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("product_detail", args=[self.product.pk]),
                                    {"action": "quick_edit", "name": "Nuevo nombre", "minimum": 7})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual((self.product.name, self.product.minimum), ("Nuevo nombre", 7))
        self.assertEqual(StockBalance.objects.get().quantity, 10)

    def test_quick_stock_keeps_product_context(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("product_detail", args=[self.product.pk]),
                                    {"action": "quick_stock", "kind": "OUT", "location": self.location.pk,
                                     "quantity": 3, "reason": "Entrega rápida"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(StockBalance.objects.get().quantity, 7)

    def test_complete_movement_form_preselects_product(self):
        self.client.force_login(self.operator)
        response = self.client.get(reverse("movements"), {"producto": self.product.pk})
        self.assertEqual(str(response.context["form"].initial["product"]), str(self.product.pk))

    def test_logout_returns_to_login(self):
        self.client.force_login(self.operator)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))

    def test_api_cannot_spoof_movement_author(self):
        api = APIClient()
        api.force_authenticate(self.operator)
        response = api.post(reverse("api-movements"), self.payload(user=self.admin.pk), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Movement.objects.latest("pk").user_id, self.operator.pk)
        self.assertEqual(response.data["delta"], -2)

    def test_api_rejects_overselling_without_writes(self):
        api = APIClient()
        api.force_authenticate(self.operator)
        response = api.post(reverse("api-movements"), self.payload(quantity=20), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(StockBalance.objects.get().quantity, 10)
        self.assertEqual(Movement.objects.count(), 1)

    def test_api_rejects_blank_reason_and_inactive_product(self):
        api = APIClient()
        api.force_authenticate(self.operator)
        self.assertEqual(api.post(reverse("api-movements"), self.payload(reason=" ")).status_code, 400)
        self.product.active = False
        self.product.save()
        self.assertEqual(api.post(reverse("api-movements"), self.payload()).status_code, 400)

    def test_api_negative_adjustment_and_display_have_one_sign(self):
        api = APIClient()
        api.force_authenticate(self.operator)
        response = api.post(reverse("api-movements"), self.payload(kind="ADJUST", quantity=-2), format="json")
        self.assertEqual(response.status_code, 201)
        self.client.force_login(self.operator)
        response = self.client.get(reverse("movements"))
        self.assertContains(response, "-2")
        self.assertNotContains(response, "−-2")

    def test_api_is_paginated_and_searchable(self):
        for n in range(30):
            Product.objects.create(sku=f"EX-{n}", name=f"Extra {n}", category=self.category)
        api = APIClient()
        api.force_authenticate(self.operator)
        response = api.get(reverse("api-products"))
        self.assertEqual(response.data["count"], 31)
        self.assertEqual(len(response.data["results"]), 25)
        response = api.get(reverse("api-products"), {"search": "P-1"})
        self.assertEqual(response.data["count"], 1)

    def test_admin_can_edit_all_catalog_fields(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("product_update", args=[self.product.pk]), {
            "sku": "P-EDITADO", "name": "Nombre actualizado", "category": self.category.pk,
            "supplier": "", "unit": "unidad", "minimum": 3,
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual((self.product.sku, self.product.unit), ("P-EDITADO", "unidad"))
        self.assertEqual(StockBalance.objects.get().quantity, 10)

    def test_unit_cannot_change_after_stock_history(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("product_update", args=[self.product.pk]), {
            "sku": self.product.sku, "name": self.product.name, "category": self.category.pk,
            "supplier": "", "unit": "pack", "minimum": 3,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La unidad no puede cambiar")
        self.product.refresh_from_db()
        self.assertEqual(self.product.unit, "unidad")

    def test_archive_keeps_history_visible_and_can_be_reversed(self):
        self.client.force_login(self.admin)
        url = reverse("product_status", args=[self.product.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {"action": "invalid"}).status_code, 400)
        self.client.post(url, {"action": "archive"})
        self.product.refresh_from_db()
        self.assertFalse(self.product.active)
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(response, "Producto archivado")
        self.assertContains(response, "Inicial")
        self.assertNotContains(response, "Guardar movimiento")
        self.assertNotContains(self.client.get(reverse("products")), "P-1")
        self.assertContains(self.client.get(reverse("products"), {"estado": "archivados"}), "P-1")
        self.client.post(url, {"action": "restore"})
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)
        self.assertEqual(StockBalance.objects.get().quantity, 10)
        self.assertEqual(Movement.objects.count(), 1)

    def test_operator_cannot_edit_full_catalog_or_archive(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.post(reverse("product_update", args=[self.product.pk]), {}).status_code, 403)
        self.assertEqual(self.client.post(reverse("product_status", args=[self.product.pk]), {"action": "archive"}).status_code, 403)
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)

    def test_archived_product_cannot_receive_stock(self):
        self.product.active = False
        self.product.save()
        self.client.force_login(self.operator)
        self.client.post(reverse("product_detail", args=[self.product.pk]), {
            "action": "quick_stock", "kind": "IN", "location": self.location.pk,
            "quantity": 3, "reason": "Intento de reposición",
        })
        self.assertEqual(StockBalance.objects.get().quantity, 10)

    def test_old_movements_are_reachable_through_pagination(self):
        for n in range(22):
            record_movement(product=self.product, location=self.location, kind="IN",
                            quantity=1, reason=f"Ingreso {n}", user=self.operator)
        self.client.force_login(self.operator)
        response = self.client.get(reverse("movements"))
        self.assertEqual(response.context["page_obj"].paginator.count, 23)
        self.assertEqual(len(response.context["movements"]), 20)
        response = self.client.get(reverse("movements"), {"page": 2})
        self.assertContains(response, "Inicial")
        detail = self.client.get(reverse("product_detail", args=[self.product.pk]), {"page": 3})
        self.assertContains(detail, "Inicial")

    def test_replenishment_filter_handles_empty_stock_and_disabled_minimum(self):
        Product.objects.create(sku="VACIO", name="Sin saldo", minimum=2, category=self.category)
        Product.objects.create(sku="SIN-ALERTA", name="Sin alerta", minimum=0, category=self.category)
        self.client.force_login(self.operator)
        response = self.client.get(reverse("products"), {"estado": "reponer"})
        self.assertContains(response, "VACIO")
        self.assertNotContains(response, "SIN-ALERTA")
        self.assertNotContains(response, "P-1")

    def test_help_and_public_login_render_without_dead_controls(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, "Cerrar sesión")
        self.client.force_login(self.operator)
        self.assertContains(self.client.get(reverse("guide")), "Corrige un conteo")
        self.assertNotContains(self.client.get(reverse("dashboard")), 'aria-label="Notificaciones"')


class DemoCommandTests(TestCase):
    @override_settings(DEBUG=True)
    def test_loading_demo_twice_keeps_history_and_balance(self):
        call_command("cargar_demo", stdout=StringIO())
        call_command("cargar_demo", stdout=StringIO())
        self.assertEqual(Product.objects.count(), 5)
        self.assertEqual(Movement.objects.count(), 5)
        self.assertEqual(sum(b.quantity for b in StockBalance.objects.all()),
                         sum(m.delta for m in Movement.objects.all()))

    @override_settings(DEBUG=False)
    def test_demo_command_is_disabled_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command("cargar_demo", stdout=StringIO())

