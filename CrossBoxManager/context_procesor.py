from .models import ClubMembership


def context_procesor(request):
    parent_club = "User not asigned to club"
    if request.user.is_authenticated:
        membership = (
            ClubMembership.objects.filter(
                user=request.user,
                status=ClubMembership.Status.ACTIVE,
            )
            .select_related("club")
            .order_by("joined_at", "pk")
            .first()
        )
        if membership:
            parent_club = membership.club.club_name
        return {"logged_user": request.user.username, "parent_club": parent_club}
    return {"logged_user": "User not logged", "parent_club": parent_club}
