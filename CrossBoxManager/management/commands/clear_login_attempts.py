from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from CrossBoxManager.models import LoginAttempt


class Command(BaseCommand):
    help = "Remove expired login rate-limit counters (schedule daily)."

    def handle(self, *args, **options):
        count, _ = LoginAttempt.objects.filter(
            started_at__lt=timezone.now()
            - timedelta(seconds=settings.LOGIN_ATTEMPT_WINDOW)
        ).delete()
        self.stdout.write(f"Removed {count} expired counters")
