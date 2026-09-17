from django.contrib import admin
from .models import (
    WeekDays,
    Hours,
    MessageTypes,
    SportClub,
    Workers,
    Athletes,
    People,
    Table,
    TreningsHarmo,
    TreningEvent,
)

from .models import ClubMembership


class PlatformAdminOnlyMixin:
    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


@admin.register(ClubMembership)
class ClubMembershipAdmin(PlatformAdminOnlyMixin, admin.ModelAdmin):
    list_display = ("user", "club", "role", "status", "joined_at")
    list_filter = ("club", "role", "status")
    readonly_fields = ("joined_at",)


@admin.register(SportClub)
class SportClubAdmin(PlatformAdminOnlyMixin, admin.ModelAdmin):
    list_display = ("club_name", "address", "nip", "bank_account")
