from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Tool


CATEGORY_STATS_CACHE_KEY = "rental:category_stats:v1"


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
@receiver(post_save, sender=Tool)
@receiver(post_delete, sender=Tool)
def invalidate_category_stats_cache(sender, **kwargs):
    cache.delete(CATEGORY_STATS_CACHE_KEY)