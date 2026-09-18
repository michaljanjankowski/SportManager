from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import ClubMembership, SportClub


class ClubAccessMixin(LoginRequiredMixin):
    allowed_roles = tuple(ClubMembership.Role.values)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.club = get_object_or_404(SportClub, pk=kwargs["sport_club_id"])
        self.membership = ClubMembership.objects.filter(
            user=request.user,
            club=self.club,
            status=ClubMembership.Status.ACTIVE,
        ).first()
        if not request.user.is_superuser and (
            self.membership is None or self.membership.role not in self.allowed_roles
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ClubManagementMixin(ClubAccessMixin):
    allowed_roles = (ClubMembership.Role.OWNER, ClubMembership.Role.MANAGER)


class SuperuserMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def can_edit_person(user, membership, person, target_role):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if membership is None or membership.status != ClubMembership.Status.ACTIVE:
        return False
    if membership.role not in (ClubMembership.Role.OWNER, ClubMembership.Role.MANAGER):
        return False
    if person.user.is_superuser or person.user.is_staff:
        return False
    if membership.role != ClubMembership.Role.OWNER and target_role in ('OWNER', 'MANAGER'):
        return False
    return not any(m.club_id != membership.club_id for m in person.user.club_memberships.all())
