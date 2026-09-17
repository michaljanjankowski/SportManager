from django.db import migrations


def migrate_memberships(apps, schema_editor):
    People = apps.get_model("CrossBoxManager", "People")
    Membership = apps.get_model("CrossBoxManager", "ClubMembership")
    alias = schema_editor.connection.alias
    for person in (
        People.objects.using(alias).exclude(sport_club=None).select_related("worker")
    ):
        role = "MEMBER"
        status = "ACTIVE"
        if person.worker_id:
            if person.worker.is_manager:
                role, status = "MANAGER", "INACTIVE"
            elif person.worker.is_trener:
                role = "COACH"
        Membership.objects.using(alias).get_or_create(
            user_id=person.user_id,
            club_id=person.sport_club_id,
            defaults={"role": role, "status": status},
        )


class Migration(migrations.Migration):
    dependencies = [("CrossBoxManager", "0003_loginattempt_clubmembership")]
    # Reverse preserves legacy data; membership rows are removed with model 0003.
    operations = [migrations.RunPython(migrate_memberships, migrations.RunPython.noop)]
