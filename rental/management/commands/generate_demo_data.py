from decimal import Decimal
from random import Random
from time import perf_counter

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from rental.models import Category, Tag, Tool


class Command(BaseCommand):
    help = "Создаёт тестовые данные для проекта «Прокат инструментов»."

    def add_arguments(self, parser):
        parser.add_argument("--tools", type=int, default=100_000)
        parser.add_argument("--batch-size", type=int, default=1_000)

    def handle(self, *args, **options):
        target_tools = options["tools"]
        batch_size = options["batch_size"]

        if target_tools < 0:
            raise CommandError("--tools не может быть меньше нуля.")
        if batch_size < 1:
            raise CommandError("--batch-size должен быть не меньше 1.")

        started = perf_counter()
        fake = Faker("ru_RU")
        fake.seed_instance(42)
        random = Random(42)

        category_names = [
            "Электроинструмент",
            "Ручной инструмент",
            "Садовая техника",
            "Измерительный инструмент",
            "Строительное оборудование",
            "Сварочное оборудование",
            "Крепёжный инструмент",
            "Оборудование для ремонта",
            "Сантехнический инструмент",
            "Автомобильный инструмент",
        ]
        category_names.extend(
            f"Категория {number:02d}"
            for number in range(len(category_names) + 1, 51)
        )

        categories = []
        for name in category_names:
            category, _ = Category.objects.get_or_create(name=name)
            categories.append(category)

        tag_names = [
            "для дома",
            "для ремонта",
            "профессиональный",
            "аккумуляторный",
            "электрический",
            "ручной",
            "для сада",
            "для стройки",
            "компактный",
            "тяжёлый",
        ]
        tag_names.extend(
            f"Тег {number:03d}"
            for number in range(len(tag_names) + 1, 201)
        )

        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)

        User = get_user_model()
        users = []

        for number in range(1, 21):
            username = f"rental_demo_{number:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.local"},
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=["password"])
            users.append(user)

        existing_tools = Tool.objects.count()
        missing_tools = max(target_tools - existing_tools, 0)
        created_tools = 0
        tagged_tools = 0
        tag_target = min(missing_tools, 1_000)
        through_model = Tool.tags.through

        while created_tools < missing_tools:
            current_size = min(batch_size, missing_tools - created_tools)
            batch = []

            for offset in range(current_size):
                number = existing_tools + created_tools + offset + 1
                batch.append(
                    Tool(
                        name=f"{fake.word().capitalize()} {number:06d}",
                        description=fake.text(max_nb_chars=240),
                        category=random.choice(categories),
                        created_by=random.choice(users),
                        is_active=(number % 10 != 0),
                        daily_rate=Decimal(random.randint(100, 5_000)),
                        late_fee_per_day=Decimal(random.randint(50, 1_000)),
                    )
                )

            with transaction.atomic():
                Tool.objects.bulk_create(batch, batch_size=current_size)

                tag_links = []
                for tool in batch:
                    if tagged_tools >= tag_target:
                        break

                    tag = random.choice(tags)
                    tag_links.append(
                        through_model(tool_id=tool.pk, tag_id=tag.pk)
                    )
                    tagged_tools += 1

                if tag_links:
                    through_model.objects.bulk_create(
                        tag_links,
                        batch_size=batch_size,
                    )

            created_tools += current_size
            self.stdout.write(
                f"Создано инструментов: {created_tools} из {missing_tools}"
            )

        elapsed = perf_counter() - started

        self.stdout.write(self.style.SUCCESS("Генерация завершена."))
        self.stdout.write(f"Категорий в базе: {Category.objects.count()}")
        self.stdout.write(f"Тегов в базе: {Tag.objects.count()}")
        self.stdout.write(f"Пользователей в базе: {User.objects.count()}")
        self.stdout.write(f"Инструментов в базе: {Tool.objects.count()}")
        self.stdout.write(f"Добавлено ссылок на теги за этот запуск: {tagged_tools}")
        self.stdout.write(f"Время выполнения: {elapsed:.2f} сек.")