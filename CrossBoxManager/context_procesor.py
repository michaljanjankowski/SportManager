from django.contrib.auth.models import User
from .models import People, SportClub


def	context_procesor(request):
    if request.user.is_authenticated:
        username = request.user.username
        user_id = request.user.id
        try:
            person = People.objects.get(user=user_id)
            parent_club = person.sport_club.club_name
        except People.DoesNotExist:
            parent_club = "User not asigned to club"
    else:
        username = "User not logged"
        parent_club = "User not asigned to club"

    return {'logged_user':username, 'parent_club':parent_club}