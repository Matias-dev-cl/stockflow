from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from apps.inventario.models import Category, Location, Movement, Product, StockBalance
from apps.inventario.services import record_movement


class InventoryServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("operador", password="local-demo-543")
        cls.category = Category.objects.create(name="Oficina")
        cls.product = Product.objects.create(sku="A-1", name="Cuaderno", category=cls.category)
        cls.location = Location.objects.create(code="B1", name="Bodega")
        record_movement(product=cls.product, location=cls.location, kind="IN",
                        quantity=10, reason="Saldo inicial", user=cls.user)

    def record(self, **kwargs):
        values = dict(product=self.product, location=self.location, kind="IN",
                      quantity=2, reason="Compra", user=self.user)
        values.update(kwargs)
        return record_movement(**values)

    def test_entry_exit_and_signed_adjustments_explain_balance(self):
        self.record(quantity=4)
        self.record(kind="OUT", quantity=3)
        self.record(kind="ADJUST", quantity=-2)
        self.record(kind="ADJUST", quantity=1)
        balance = StockBalance.objects.get(product=self.product, location=self.location)
        self.assertEqual(balance.quantity, 10)
        self.assertEqual(balance.quantity, sum(m.delta for m in Movement.objects.all()))

    def test_insufficient_stock_leaves_balance_and_history_unchanged(self):
        with self.assertRaises(ValidationError):
            self.record(kind="OUT", quantity=11)
        self.assertEqual(StockBalance.objects.get().quantity, 10)
        self.assertEqual(Movement.objects.count(), 1)

    def test_negative_adjustment_cannot_take_balance_below_zero(self):
        with self.assertRaises(ValidationError):
            self.record(kind="ADJUST", quantity=-11)
        self.assertEqual(StockBalance.objects.get().quantity, 10)

    def test_failed_first_exit_does_not_leave_empty_balance(self):
        location = Location.objects.create(code="B2", name="Segunda bodega")
        with self.assertRaises(ValidationError):
            self.record(location=location, kind="OUT", quantity=1)
        self.assertFalse(StockBalance.objects.filter(location=location).exists())

    def test_invalid_quantities_are_rejected_in_the_service(self):
        for kind, quantity in [("IN", 0), ("OUT", -2), ("ADJUST", 0),
                               ("IN", True), ("IN", 1.5), ("IN", 2**31)]:
            with self.subTest(kind=kind, quantity=quantity), self.assertRaises(ValidationError):
                self.record(kind=kind, quantity=quantity)
        self.assertEqual(Movement.objects.count(), 1)

    def test_blank_or_oversized_reason_is_rejected(self):
        for reason in [" ", "", "x" * 241]:
            with self.subTest(reason=reason), self.assertRaises(ValidationError):
                self.record(reason=reason)

    def test_resulting_balance_cannot_overflow_database_integer(self):
        with self.assertRaises(ValidationError):
            self.record(quantity=2**31 - 1)

    def test_inactive_entities_and_users_cannot_create_movements(self):
        self.product.active = False
        with self.assertRaises(ValidationError):
            self.record()
        self.product.active = True
        self.location.active = False
        with self.assertRaises(ValidationError):
            self.record()
        self.location.active = True
        self.user.is_active = False
        with self.assertRaises(ValidationError):
            self.record()

    def test_history_insert_is_rolled_back_if_saving_balance_fails(self):
        with patch.object(StockBalance, "save", side_effect=RuntimeError("Simulated write failure")):
            with self.assertRaises(RuntimeError):
                self.record()
        self.assertEqual(Movement.objects.count(), 1)
        self.assertEqual(StockBalance.objects.get().quantity, 10)

    def test_database_rejects_invalid_kind_or_quantity(self):
        for kind, quantity in [("OUT", -1), ("IN", 0), ("ADJUST", 0), ("UNKNOWN", 1)]:
            with self.subTest(kind=kind, quantity=quantity):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Movement.objects.create(product=self.product, location=self.location,
                                            kind=kind, quantity=quantity, reason="Invalid", user=self.user)

    def test_display_sign_comes_from_actual_stock_effect(self):
        negative, _ = self.record(kind="ADJUST", quantity=-2)
        outgoing, _ = self.record(kind="OUT", quantity=3)
        positive, _ = self.record(kind="ADJUST", quantity=1)
        self.assertEqual(negative.signed_quantity, "-2")
        self.assertEqual(outgoing.signed_quantity, "-3")
        self.assertEqual(positive.signed_quantity, "+1")


class ConcurrentStockTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_simultaneous_exits_cannot_oversell(self):
        user = get_user_model().objects.create_user("concurrente")
        category = Category.objects.create(name="Prueba")
        product = Product.objects.create(sku="CON-1", name="Producto", category=category)
        location = Location.objects.create(code="CON", name="Bodega")
        record_movement(product=product, location=location, kind="IN", quantity=10,
                        reason="Inicial", user=user)
        barrier = Barrier(2)

        def withdraw():
            close_old_connections()
            try:
                worker_product = Product.objects.get(pk=product.pk)
                worker_location = Location.objects.get(pk=location.pk)
                worker_user = get_user_model().objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                try:
                    record_movement(product=worker_product, location=worker_location,
                                    kind="OUT", quantity=7, reason="Salida simultánea", user=worker_user)
                    return "ok"
                except ValidationError:
                    return "insufficient"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: withdraw(), range(2)))
        self.assertCountEqual(results, ["ok", "insufficient"])
        self.assertEqual(StockBalance.objects.get().quantity, 3)
        self.assertEqual(Movement.objects.count(), 2)

