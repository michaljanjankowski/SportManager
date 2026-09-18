from django import template
from CrossBoxManager.models import ClubMembership

register = template.Library()


@register.simple_tag(takes_context=True)
def club_action_allowed(context, club, action):
    user = context['request'].user
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return action in ('manage', 'people', 'messages')
    cache = context.render_context.setdefault('club_roles', {})
    if club.pk not in cache:
        cache[club.pk] = ClubMembership.objects.filter(
            user=user, club=club, status=ClubMembership.Status.ACTIVE
        ).values_list('role', flat=True).first()
    role = cache[club.pk]
    allowed = {
        'manage': ('OWNER', 'MANAGER'),
        'people': ('OWNER', 'MANAGER', 'COACH'),
        'messages': tuple(ClubMembership.Role.values),
    }
    return role is not None and role in allowed.get(action, ())
