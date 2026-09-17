import hashlib
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import LoginAttempt


def consume_attempt(scope, value, limit):
    key = hashlib.sha256(f"{scope}:{value}".encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        LoginAttempt.objects.get_or_create(key=key, defaults={"started_at": now})
        counter = LoginAttempt.objects.select_for_update().get(key=key)
        if counter.started_at <= now - timedelta(seconds=settings.LOGIN_ATTEMPT_WINDOW):
            counter.started_at = now
            counter.count = 0
            counter.save(update_fields=["started_at", "count"])
        # Conditional update also prevents exceeding the limit on SQLite.
        return bool(
            LoginAttempt.objects.filter(pk=counter.pk, count__lt=limit).update(
                count=F("count") + 1
            )
        )


class RateLimitedBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is not None:
            # REMOTE_ADDR comes from the server; never trust client forwarding headers.
            address = request.META.get("REMOTE_ADDR", "unknown")
            ip_allowed = consume_attempt("ip", address, settings.LOGIN_IP_LIMIT)
            if not ip_allowed:
                return None
            account_allowed = consume_attempt(
                "account", username or "", settings.LOGIN_ACCOUNT_LIMIT
            )
            if not account_allowed:
                return None
        return super().authenticate(
            request, username=username, password=password, **kwargs
        )
