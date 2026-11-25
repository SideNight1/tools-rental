from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q

from .models import Rental, Tool


def get_available_tools(start_date, end_date):
    """Возвращает активные инструменты, свободные в выбранный период."""
    if end_date < start_date:
        raise ValidationError(
            "Дата окончания не может быть раньше даты начала."
        )

    conflicting_rentals = (
        Rental.objects
        .filter(
            tool_id=OuterRef("pk"),
            start_date__lte=end_date,
        )
        .exclude(status=Rental.Status.CANCELLED)
        .filter(
            Q(actual_return_date__gte=start_date)
            | Q(
                actual_return_date__isnull=True,
                end_date__gte=start_date,
            )
            | Q(
                status=Rental.Status.ACTIVE,
                actual_return_date__isnull=True,
                end_date__lt=start_date,
            )
        )
    )

    return (
        Tool.objects
        .filter(is_active=True)
        .annotate(has_conflict=Exists(conflicting_rentals))
        .filter(has_conflict=False)
        .select_related("category", "created_by")
        .prefetch_related("tags")
        .order_by("name", "pk")
    )


def calculate_rental_amounts(tool, start_date, end_date, returned_on=None):
    """Считает стоимость аренды и штраф по тарифам инструмента."""
    if end_date < start_date:
        raise ValidationError(
            "Дата окончания не может быть раньше даты начала."
        )

    if returned_on and returned_on < start_date:
        raise ValidationError(
            "Дата возврата не может быть раньше даты начала аренды."
        )

    rental = Rental(
        tool=tool,
        start_date=start_date,
        end_date=end_date,
        daily_rate=tool.daily_rate,
        late_fee_per_day=tool.late_fee_per_day,
    )

    return rental.calculate_amounts(returned_on=returned_on)
