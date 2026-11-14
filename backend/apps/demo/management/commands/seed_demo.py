from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.demo.seed import seed_demo
from config.env import required


class Command(BaseCommand):
    help = "Create demo users and tasks, only if the database has no users yet."

    def handle(self, *args: Any, **options: Any) -> None:
        result = seed_demo(password=required("DEMO_PASSWORD"), now=timezone.now())
        if result is None:
            self.stdout.write("The database already has users; nothing seeded.")
        else:
            self.stdout.write(f"Seeded {result.users} users and {result.tasks} tasks.")
