from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField("Название", max_length=50, unique=True)

    def __str__(self):
        return self.name


class Tool(models.Model):
    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tools",
        verbose_name="Категория",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="tools",
        verbose_name="Теги",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tools_created",
        verbose_name="Добавил",
    )
    is_active = models.BooleanField("Доступен в каталоге", default=True)
    daily_rate = models.DecimalField(
        "Стоимость за день",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    late_fee_per_day = models.DecimalField(
        "Штраф за день просрочки",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата изменения", auto_now=True)
    class Meta:
        indexes = [
            models.Index(
                fields=["category", "name", "id"],
                condition=models.Q(is_active=True),
                name="tool_act_cat_name_id",
            ),
            models.Index(
                fields=["name", "id"],
                condition=models.Q(is_active=True),
                name="tool_act_name_id",
            ),
        ]
    def __str__(self):
        return self.name


class Rental(models.Model):
    class Status(models.TextChoices):
        RESERVED = "reserved", "Забронирована"
        ACTIVE = "active", "Выдана"
        RETURNED = "returned", "Возвращена"
        CANCELLED = "cancelled", "Отменена"

    tool = models.ForeignKey(
        Tool,
        on_delete=models.PROTECT,
        related_name="rentals",
        verbose_name="Инструмент",
    )
    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tool_rentals",
        verbose_name="Арендатор",
    )
    start_date = models.DateField("Дата начала аренды")
    end_date = models.DateField("Плановая дата возврата")
    actual_return_date = models.DateField(
        "Фактическая дата возврата",
        null=True,
        blank=True,
    )
    status = models.CharField(
        "Статус",
        max_length=12,
        choices=Status.choices,
        default=Status.RESERVED,
    )
    daily_rate = models.DecimalField(
        "Ставка за день на момент аренды",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    late_fee_per_day = models.DecimalField(
        "Штраф за день на момент аренды",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def calculate_amounts(self, returned_on=None):
        """Считает аренду по дням и штраф за просрочку."""
        rental_days = (self.end_date - self.start_date).days + 1
        return_date = returned_on or self.actual_return_date
        late_days = (
            max(0, (return_date - self.end_date).days)
            if return_date
            else 0
        )
        rental_cost = self.daily_rate * rental_days
        late_fee = self.late_fee_per_day * late_days

        return {
            "rental_days": rental_days,
            "rental_cost": rental_cost,
            "late_days": late_days,
            "late_fee": late_fee,
            "total": rental_cost + late_fee,
        }

    def __str__(self):
        return f"{self.tool.name}: {self.start_date} — {self.end_date}"