from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Rental, Tag, Tool
from .services import calculate_rental_amounts, get_available_tools


class RentalFeaturesTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="rental_test_user",
            password="test-password-only",
        )
        self.category = Category.objects.create(name="Тестовая категория")
        self.tag = Tag.objects.create(name="Тестовый тег")
        self.tool = Tool.objects.create(
            name="Тестовая дрель",
            description="Инструмент для автоматических тестов",
            category=self.category,
            created_by=self.user,
            is_active=True,
            daily_rate=Decimal("100.00"),
            late_fee_per_day=Decimal("25.00"),
        )
        self.tool.tags.add(self.tag)

        self.start_date = date(2030, 1, 10)
        self.end_date = date(2030, 1, 12)

    def test_tool_is_available_without_rentals(self):
        available = get_available_tools(
            self.start_date,
            self.end_date,
        ).filter(pk=self.tool.pk).exists()

        self.assertTrue(available)

    def test_overlapping_rental_makes_tool_unavailable(self):
        Rental.objects.create(
            tool=self.tool,
            renter=self.user,
            start_date=self.start_date,
            end_date=self.end_date,
            status=Rental.Status.RESERVED,
            daily_rate=self.tool.daily_rate,
            late_fee_per_day=self.tool.late_fee_per_day,
        )

        available = get_available_tools(
            self.start_date,
            self.end_date,
        ).filter(pk=self.tool.pk).exists()

        self.assertFalse(available)

    def test_cancelled_rental_does_not_block_tool(self):
        Rental.objects.create(
            tool=self.tool,
            renter=self.user,
            start_date=self.start_date,
            end_date=self.end_date,
            status=Rental.Status.CANCELLED,
            daily_rate=self.tool.daily_rate,
            late_fee_per_day=self.tool.late_fee_per_day,
        )

        available = get_available_tools(
            self.start_date,
            self.end_date,
        ).filter(pk=self.tool.pk).exists()

        self.assertTrue(available)

    def test_cost_includes_rental_days_and_late_fee(self):
        result = calculate_rental_amounts(
            tool=self.tool,
            start_date=self.start_date,
            end_date=self.end_date,
            returned_on=date(2030, 1, 14),
        )

        self.assertEqual(result["rental_days"], 3)
        self.assertEqual(result["rental_cost"], Decimal("300.00"))
        self.assertEqual(result["late_days"], 2)
        self.assertEqual(result["late_fee"], Decimal("50.00"))
        self.assertEqual(result["total"], Decimal("350.00"))

    def test_catalog_page_uses_four_queries(self):
        with self.assertNumQueries(4):
            response = self.client.get(reverse("rental:tool_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tool.name)