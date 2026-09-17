from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import ClubMembership, LoginAttempt, People, SportClub, Workers, Table


class SecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = SportClub.objects.create(club_name="A", bank_account="original")
        cls.other = SportClub.objects.create(club_name="B", bank_account="private")
        cls.users = {}
        for role in ClubMembership.Role.values:
            user = User.objects.create_user(
                username=role.lower(), password="Secure-pilot-password-928!"
            )
            ClubMembership.objects.create(user=user, club=cls.club, role=role)
            People.objects.create(
                user=user, sport_club=cls.club, worker=Workers.objects.create()
            )
            cls.users[role] = user
        cls.outsider = User.objects.create_user(username="outsider")
        cls.foreign = People.objects.create(user=cls.outsider, sport_club=cls.other)
        ClubMembership.objects.create(user=cls.outsider, club=cls.other)

    def urls(self, club):
        return [
            reverse(name, args=[club.pk])
            for name in (
                "sport_club_details_by_id",
                "sport_club_modify_by_id",
                "people_show_by_club_id",
                "athlete_add_by_club_id",
                "worker_add_by_club_id",
                "msg_show_to_person",
                "all_messages_in_club_show",
            )
        ]

    def test_anonymous_cannot_access_any_club_endpoint(self):
        urls = self.urls(self.club) + [
            reverse(
                "person_in_club_modify_by_id", args=[self.club.pk, self.foreign.pk]
            ),
            reverse("send_message", args=[self.club.pk, self.foreign.pk]),
            reverse("sport_club_add"),
        ]
        for url in urls:
            for method in ("get", "post"):
                with self.subTest(url=url, method=method):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 302)
        self.assertEqual(User.objects.count(), 5)

    def test_all_roles_are_denied_other_club_get_and_post(self):
        urls = self.urls(self.other) + [
            reverse(
                "person_in_club_modify_by_id", args=[self.other.pk, self.foreign.pk]
            ),
            reverse("send_message", args=[self.other.pk, self.foreign.pk]),
        ]
        for user in self.users.values():
            self.client.force_login(user)
            for url in urls:
                for method in ("get", "post"):
                    with self.subTest(user=user.username, url=url, method=method):
                        self.assertEqual(
                            getattr(self.client, method)(url).status_code, 403
                        )
        self.other.refresh_from_db()
        self.assertEqual(self.other.bank_account, "private")
        self.assertFalse(Table.objects.exists())

    def test_member_and_coach_cannot_manage_club_or_accounts(self):
        for role in ("MEMBER", "COACH"):
            self.client.force_login(self.users[role])
            for name in (
                "sport_club_modify_by_id",
                "athlete_add_by_club_id",
                "worker_add_by_club_id",
            ):
                for method in ("get", "post"):
                    self.assertEqual(
                        getattr(self.client, method)(
                            reverse(name, args=[self.club.pk])
                        ).status_code,
                        403,
                    )
            self.assertEqual(
                self.client.post(reverse("sport_club_add")).status_code, 403
            )
        self.club.refresh_from_db()
        self.assertEqual(self.club.bank_account, "original")

    def test_club_list_is_scoped(self):
        self.client.force_login(self.users["MEMBER"])
        self.assertEqual(
            list(self.client.get(reverse("sport_clubs_show")).context["clubs"]),
            [self.club],
        )

    def test_inactive_membership_and_legacy_flags_grant_no_access(self):
        user = self.users["MANAGER"]
        ClubMembership.objects.filter(user=user).update(status="INACTIVE")
        Workers.objects.filter(people__user=user).update(is_manager=True)
        self.client.force_login(user)
        for url in self.urls(self.club):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            list(self.client.get(reverse("sport_clubs_show")).context["clubs"]), []
        )

    def test_target_from_other_club_returns_404(self):
        self.client.force_login(self.users["OWNER"])
        for name in ("person_in_club_modify_by_id", "send_message"):
            url = reverse(name, args=[self.club.pk, self.foreign.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url).status_code, 404)

    def person_data(self, role="COACH", password="Safe-random-pass-961!"):
        return {
            "username": "newperson",
            "first_name": "Test",
            "last_name": "User",
            "email": "new@example.com",
            "password": password,
            "role": role,
        }

    def test_manager_cannot_assign_owner_or_manager(self):
        self.client.force_login(self.users["MANAGER"])
        url = reverse("worker_add_by_club_id", args=[self.club.pk])
        for role in ("OWNER", "MANAGER"):
            response = self.client.post(url, self.person_data(role))
            self.assertTrue(response.context["personaddform"].errors)
            self.assertFalse(User.objects.filter(username="newperson").exists())
        self.client.post(url, self.person_data())
        self.assertEqual(
            ClubMembership.objects.get(user__username="newperson").role, "COACH"
        )

    def test_manager_cannot_edit_owner_or_promote_coach(self):
        self.client.force_login(self.users["MANAGER"])
        owner = People.objects.get(user=self.users["OWNER"])
        url = reverse("person_in_club_modify_by_id", args=[self.club.pk, owner.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, self.person_data()).status_code, 403)
        coach = People.objects.get(user=self.users["COACH"])
        response = self.client.post(
            reverse("person_in_club_modify_by_id", args=[self.club.pk, coach.pk]),
            self.person_data("OWNER"),
        )
        self.assertTrue(response.context["personmodyfieform"].errors)
        self.assertEqual(ClubMembership.objects.get(user=coach.user).role, "COACH")

    def test_manager_can_update_identity_without_touching_django_permissions(self):
        self.client.force_login(self.users["MANAGER"])
        coach = People.objects.get(user=self.users["COACH"])
        data = self.person_data()
        data.update(is_superuser="on", is_staff="on")
        response = self.client.post(
            reverse("person_in_club_modify_by_id", args=[self.club.pk, coach.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        coach.user.refresh_from_db()
        self.assertEqual(coach.user.username, "newperson")
        self.assertFalse(coach.user.is_superuser)
        self.assertFalse(coach.user.is_staff)

    def test_multi_club_identity_cannot_be_modified_by_club_owner(self):
        coach = self.users["COACH"]
        ClubMembership.objects.create(user=coach, club=self.other)
        self.client.force_login(self.users["OWNER"])
        url = reverse(
            "person_in_club_modify_by_id",
            args=[self.club.pk, People.objects.get(user=coach).pk],
        )
        self.assertEqual(self.client.post(url, self.person_data()).status_code, 403)

    def test_weak_passwords_rejected_in_both_creation_forms(self):
        self.client.force_login(self.users["OWNER"])
        for name in ("athlete_add_by_club_id", "worker_add_by_club_id"):
            response = self.client.post(
                reverse(name, args=[self.club.pk]), self.person_data(password="x")
            )
            self.assertIn("password", response.context["personaddform"].errors)
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_creation_rolls_back_on_membership_failure(self):
        self.client.force_login(self.users["OWNER"])
        with patch(
            "CrossBoxManager.views.ClubMembership.objects.create",
            side_effect=IntegrityError,
        ):
            with self.assertRaises(IntegrityError):
                self.client.post(
                    reverse("worker_add_by_club_id", args=[self.club.pk]),
                    self.person_data(),
                )
        self.assertFalse(User.objects.filter(username="newperson").exists())

    def test_logout_requires_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.users["MEMBER"])
        self.assertEqual(client.get(reverse("logout_page")).status_code, 405)
        self.assertEqual(client.post(reverse("logout_page")).status_code, 403)
        response = client.get(reverse("sport_club_details_by_id", args=[self.club.pk]))
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(
            client.post(
                reverse("logout_page"),
                {"csrfmiddlewaretoken": client.cookies["csrftoken"].value},
            ).status_code,
            302,
        )
        self.assertNotIn("_auth_user_id", client.session)

    def test_membership_constraints(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClubMembership.objects.create(user=self.users["MEMBER"], club=self.club)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClubMembership.objects.filter(user=self.users["MEMBER"]).update(
                role="INVALID"
            )

    def test_exact_public_paths(self):
        self.assertEqual(self.client.get("/login/").status_code, 200)
        for path in ("/login/extra", "/athlete_add/1/", "/administer/", "/random/"):
            self.assertEqual(self.client.get(path).status_code, 302)
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)


@override_settings(LOGIN_ACCOUNT_LIMIT=2, LOGIN_IP_LIMIT=3)
class LoginRateLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser", password="Valid-password-861!"
        )

    def login(
        self, username="loginuser", password="wrong", ip="127.0.0.1", path="/login/"
    ):
        fields = (
            {"user_name": username, "password": password}
            if path == "/login/"
            else {"username": username, "password": password}
        )
        return self.client.post(
            path, fields, REMOTE_ADDR=ip, HTTP_X_FORWARDED_FOR="spoofed"
        )

    def test_account_limit_shared_between_ips_and_admin(self):
        self.login(ip="1.1.1.1")
        self.login(ip="2.2.2.2", path="/admin/login/")
        self.login(ip="3.3.3.3", password="Valid-password-861!")
        self.assertNotIn("_auth_user_id", self.client.session)
        LoginAttempt.objects.update(started_at=timezone.now() - timedelta(seconds=901))
        self.assertEqual(self.login(password="Valid-password-861!").status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_source_limit_applies_across_accounts(self):
        for username in ("a", "b", "c"):
            self.login(username=username)
        self.login(password="Valid-password-861!")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.login(password="Valid-password-861!")
        self.assertNotIn("_auth_user_id", self.client.session)


from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, SimpleTestCase
import os
import subprocess
import sys


class MembershipMigrationTests(TransactionTestCase):
    def test_legacy_roles_migrate_without_activating_managers(self):
        executor = MigrationExecutor(connection)
        before = [("CrossBoxManager", "0003_loginattempt_clubmembership")]
        after = [("CrossBoxManager", "0004_migrate_club_memberships")]
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        Club = apps.get_model("CrossBoxManager", "SportClub")
        Person = apps.get_model("CrossBoxManager", "People")
        Worker = apps.get_model("CrossBoxManager", "Workers")
        LegacyUser = apps.get_model("auth", "User")
        club = Club.objects.create(club_name="Legacy")
        try:
            for name, flags in [
                ("manager", {"is_manager": True}),
                ("coach", {"is_trener": True}),
                ("accountant", {"is_accountant": True, "is_trener": False}),
                ("member", None),
            ]:
                user = LegacyUser.objects.create(username=name)
                worker = Worker.objects.create(**flags) if flags else None
                Person.objects.create(user=user, sport_club=club, worker=worker)
            Person.objects.create(user=LegacyUser.objects.create(username="unassigned"))
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            Membership = executor.loader.project_state(after).apps.get_model(
                "CrossBoxManager", "ClubMembership"
            )
            actual = {
                m.user.username: (m.role, m.status)
                for m in Membership.objects.select_related("user")
            }
            self.assertEqual(
                actual,
                {
                    "manager": ("MANAGER", "INACTIVE"),
                    "coach": ("COACH", "ACTIVE"),
                    "accountant": ("MEMBER", "ACTIVE"),
                    "member": ("MEMBER", "ACTIVE"),
                },
            )
        finally:
            MigrationExecutor(connection).migrate(after)


class ProductionConfigurationTests(SimpleTestCase):
    def load_settings(self, **values):
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("DJANGO_")
        }
        env.update(values)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "from SportManager import settings; assert not settings.DEBUG; "
                "assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE; "
                "assert settings.SECURE_SSL_REDIRECT; assert settings.SECURE_HSTS_SECONDS > 0",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_secret_fails_closed(self):
        result = self.load_settings(DJANGO_ALLOWED_HOSTS="example.invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set DJANGO_SECRET_KEY", result.stderr)

    def test_missing_hosts_fails_closed(self):
        result = self.load_settings(DJANGO_SECRET_KEY="test-only-external-secret")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit DJANGO_ALLOWED_HOSTS", result.stderr)

    def test_production_defaults_secure(self):
        result = self.load_settings(
            DJANGO_SECRET_KEY="test-only-external-secret",
            DJANGO_ALLOWED_HOSTS="example.invalid",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
