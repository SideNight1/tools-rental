from django.core.cache import cache
from django.db.models import Count, Q

from .models import Category


CATEGORY_STATS_CACHE_KEY = "rental:category_stats:v1"
CATEGORY_STATS_CACHE_TIMEOUT = 300


def get_category_stats():
    """Возвращает число инструментов в категориях, используя кэш."""
    def load_stats():
        return list(
            Category.objects
            .order_by("name")
            .annotate(
                tool_count=Count("tools"),
                active_tool_count=Count(
                    "tools",
                    filter=Q(tools__is_active=True),
                ),
            )
            .values(
                "id",
                "name",
                "tool_count",
                "active_tool_count",
            )
        )

    return cache.get_or_set(
        CATEGORY_STATS_CACHE_KEY,
        load_stats,
        timeout=CATEGORY_STATS_CACHE_TIMEOUT,
    )


def invalidate_category_stats():
    """Удаляет сохранённую сводку, чтобы её пересчитали при следующем запросе."""
    cache.delete(CATEGORY_STATS_CACHE_KEY)