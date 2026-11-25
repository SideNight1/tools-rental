from django import forms
from django.utils import timezone

from .models import Tool


class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = (
            "name",
            "description",
            "category",
            "tags",
            "is_active",
            "daily_rate",
            "late_fee_per_day",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class AvailabilityForm(forms.Form):
    start_date = forms.DateField(
        label="Дата начала",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Дата окончания",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and start_date < timezone.localdate():
            self.add_error("start_date", "Выбери сегодняшнюю или будущую дату.")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "Дата окончания не может быть раньше начала.")

        return cleaned_data


class CostCalculatorForm(forms.Form):
    tool = forms.CharField(
        label="Инструмент — вставь точное название из каталога",
        max_length=200,
    )
    start_date = forms.DateField(
        label="Дата начала",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="Плановая дата возврата",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    returned_on = forms.DateField(
        label="Фактическая дата возврата",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean_tool(self):
        name = self.cleaned_data["tool"].strip()
        matches = list(
            Tool.objects
            .filter(name__iexact=name, is_active=True)
            .order_by("pk")[:2]
        )

        if not matches:
            raise forms.ValidationError(
                "Активный инструмент с таким названием не найден."
            )

        if len(matches) > 1:
            raise forms.ValidationError(
                "Найдено несколько инструментов с таким названием."
            )

        return matches[0]

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        returned_on = cleaned_data.get("returned_on")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "Дата возврата не может быть раньше начала аренды.",
            )

        if start_date and returned_on and returned_on < start_date:
            self.add_error(
                "returned_on",
                "Фактическая дата возврата не может быть раньше начала аренды.",
            )

        return cleaned_data