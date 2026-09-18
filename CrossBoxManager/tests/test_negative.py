"""Negative request tests verify rejection and absence of partial writes."""

from django.contrib.auth.models import Permission, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import (
    Athletes,
    ClubMembership,
    LoginAttempt,
    People,
    SportClub,
    Table,
    Workers,
)


class NegativeRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.club = SportClub.objects.create(
            club_name="Negative cases",
            address="Address",
            nip="123",
            bank_account="original",
            founder="Founder",
            description="Description",
        )
        cls.other = SportClub.objects.create(club_name="Foreign club")
        cls.users = {}
        cls.people = {}
        for role in ClubMembership.Role.values:
            user = User.objects.create_user(username="negative_" + role.lower())
            cls.users[role] = user
            cls.people[role] = People.objects.create(
                user=user,
                sport_club=cls.club,
                worker=Workers.objects.create(),
            )
            ClubMembership.objects.create(user=user, club=cls.club, role=role)
        cls.foreign_user = User.objects.create_user(username="foreign_target")
        cls.foreign_person = People.objects.create(
            user=cls.foreign_user, sport_club=cls.other
        )
        ClubMembership.objects.create(user=cls.foreign_user, club=cls.other)
        cls.admin = User.objects.create_superuser(username="negative_admin")

    def snapshot(self):
        return {
            model.__name__: list(model.objects.order_by("pk").values())
            for model in (
                User,
                SportClub,
                People,
                Workers,
                Athletes,
                ClubMembership,
                Table,
            )
        }

    def person_data(self, **changes):
        data = {
            "username": "new_negative_user",
            "first_name": "Changed",
            "last_name": "Person",
            "email": "new@example.com",
            "password": "Unrelated-secure-secret-925!",
            "role": "COACH",
        }
        data.update(changes)
        return data

    def club_data(self, **changes):
        data = {
            "club_name": self.club.club_name,
            "address": "Changed address",
            "nip": "456",
            "bank_account": "attacker-account",
            "founder": "Changed",
            "description": "Changed",
        }
        data.update(changes)
        return data

    def mutation_requests(self):
        return [
            (reverse("sport_club_modify_by_id", args=[self.club.pk]), self.club_data()),
            (
                reverse("athlete_add_by_club_id", args=[self.club.pk]),
                self.person_data(),
            ),
            (
                reverse("worker_add_by_club_id", args=[self.club.pk]),
                self.person_data(role="OWNER"),
            ),
            (
                reverse(
                    "person_in_club_modify_by_id",
                    args=[self.club.pk, self.people["COACH"].pk],
                ),
                self.person_data(),
            ),
        ]

    def test_valid_payloads_do_not_bypass_member_or_coach_permissions(self):
        for role in ("MEMBER", "COACH"):
            self.client.force_login(self.users[role])
            before = self.snapshot()
            for url, data in self.mutation_requests():
                with self.subTest(role=role, url=url):
                    self.assertEqual(self.client.post(url, data).status_code, 403)
                    self.assertEqual(self.snapshot(), before)

    def test_valid_anonymous_creation_payload_creates_nothing(self):
        before = self.snapshot()
        for name in ("athlete_add_by_club_id", "worker_add_by_club_id"):
            response = self.client.post(
                reverse(name, args=[self.club.pk]), self.person_data(role="OWNER")
            )
            self.assertRedirects(
                response, reverse("login_page"), fetch_redirect_response=False
            )
            self.assertEqual(self.snapshot(), before)

    def test_legacy_profile_without_membership_cannot_send_or_modify(self):
        ClubMembership.objects.filter(user=self.users["MANAGER"]).delete()
        Workers.objects.filter(pk=self.people["MANAGER"].worker_id).update(
            is_manager=True
        )
        self.client.force_login(self.users["MANAGER"])
        before = self.snapshot()
        requests = self.mutation_requests() + [
            (
                reverse("send_message", args=[self.club.pk, self.people["MEMBER"].pk]),
                {"message": "Unauthorized", "typeOfmessage": "InterStaff"},
            )
        ]
        for url, data in requests:
            self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_membership_revoked_during_session_denies_next_request(self):
        self.client.force_login(self.users["MANAGER"])
        url = reverse("sport_club_modify_by_id", args=[self.club.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        for revoke in ("inactive", "deleted"):
            if revoke == "inactive":
                ClubMembership.objects.filter(user=self.users["MANAGER"]).update(
                    status="INACTIVE"
                )
            else:
                ClubMembership.objects.filter(user=self.users["MANAGER"]).delete()
            before = self.snapshot()
            self.assertEqual(self.client.post(url, self.club_data()).status_code, 403)
            self.assertEqual(self.snapshot(), before)

    def test_role_downgrade_during_session_removes_management_actions(self):
        self.client.force_login(self.users["MANAGER"])
        ClubMembership.objects.filter(user=self.users["MANAGER"]).update(role="MEMBER")
        before = self.snapshot()
        for url, data in self.mutation_requests():
            self.assertEqual(self.client.post(url, data).status_code, 403)
        response = self.client.get(
            reverse("sport_club_details_by_id", args=[self.club.pk])
        )
        self.assertNotContains(
            response,
            'href="' + reverse("worker_add_by_club_id", args=[self.club.pk]) + '"',
        )
        self.assertEqual(self.snapshot(), before)

    def test_csrf_missing_or_invalid_blocks_all_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.users["OWNER"])
        client.get(reverse("sport_club_details_by_id", args=[self.club.pk]))
        before = self.snapshot()
        requests = self.mutation_requests() + [
            (
                reverse("send_message", args=[self.club.pk, self.people["MEMBER"].pk]),
                {"message": "Rejected", "typeOfmessage": "InterStaff"},
            ),
        ]
        for url, data in requests:
            for token in (None, "x" * 32):
                payload = dict(data)
                if token is not None:
                    payload["csrfmiddlewaretoken"] = token
                with self.subTest(url=url, token=token):
                    self.assertEqual(client.post(url, payload).status_code, 403)
                    self.assertEqual(self.snapshot(), before)
        client.force_login(self.admin)
        before = self.snapshot()
        self.assertEqual(
            client.post(
                reverse("sport_club_add"), self.club_data(club_name="Forged club")
            ).status_code,
            403,
        )
        self.assertEqual(self.snapshot(), before)

    def test_unsupported_methods_do_not_write(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        for url, _ in self.mutation_requests():
            for method in ("put", "patch", "delete"):
                with self.subTest(url=url, method=method):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertEqual(self.snapshot(), before)

    def test_missing_and_malformed_ids_return_404_without_writes(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        for value in (0, 999999, "invalid", -1):
            for path in (
                f"/club_modify/{value}",
                f"/person_modify/{self.club.pk}/{value}",
                f"/message_add/{self.club.pk}/{value}",
            ):
                with self.subTest(path=path):
                    self.assertEqual(
                        self.client.post(path, self.person_data()).status_code, 404
                    )
        self.assertEqual(self.snapshot(), before)

    def test_invalid_creation_inputs_leave_no_partial_profiles(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        cases = (
            {"username": ""},
            {"username": "bad username!"},
            {"username": "x" * 151},
            {"username": self.foreign_user.username},
            {"email": "not-an-email"},
            {"password": ""},
            {"password": "123456789012345"},
            {"password": "new_negative_user"},
        )
        for name in ("athlete_add_by_club_id", "worker_add_by_club_id"):
            for changes in cases:
                with self.subTest(endpoint=name, changes=changes):
                    response = self.client.post(
                        reverse(name, args=[self.club.pk]), self.person_data(**changes)
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["personaddform"].errors)
                    self.assertEqual(self.snapshot(), before)

    def test_unknown_or_missing_staff_role_is_rejected(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        for role in ("", "ADMIN", "owner", "SUPERUSER"):
            response = self.client.post(
                reverse("worker_add_by_club_id", args=[self.club.pk]),
                self.person_data(role=role),
            )
            self.assertIn("role", response.context["personaddform"].errors)
            self.assertEqual(self.snapshot(), before)

    def test_invalid_identity_edit_does_not_change_role_or_identity(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        url = reverse(
            "person_in_club_modify_by_id", args=[self.club.pk, self.people["COACH"].pk]
        )
        for changes in (
            {"username": self.foreign_user.username},
            {"email": "invalid"},
            {"role": "ADMIN"},
        ):
            response = self.client.post(url, self.person_data(**changes))
            self.assertTrue(response.context["personmodyfieform"].errors)
            self.assertEqual(self.snapshot(), before)

    def test_owner_cannot_demote_self_or_another_owner(self):
        self.client.force_login(self.users["OWNER"])
        second_owner = User.objects.create_user(username="second_owner")
        person = People.objects.create(
            user=second_owner, worker=Workers.objects.create(), sport_club=self.club
        )
        ClubMembership.objects.create(user=second_owner, club=self.club, role="OWNER")
        before = self.snapshot()
        for target in (self.people["OWNER"], person):
            response = self.client.post(
                reverse("person_in_club_modify_by_id", args=[self.club.pk, target.pk]),
                self.person_data(username=target.user.username, role="MEMBER"),
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(self.snapshot(), before)

    def test_club_owner_cannot_edit_platform_staff_or_superuser(self):
        self.client.force_login(self.users["OWNER"])
        target = self.users["COACH"]
        for flag in ("is_staff", "is_superuser"):
            setattr(target, flag, True)
            target.save()
            before = self.snapshot()
            url = reverse(
                "person_in_club_modify_by_id",
                args=[self.club.pk, self.people["COACH"].pk],
            )
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.person_data()).status_code, 403)
            self.assertEqual(self.snapshot(), before)
            setattr(target, flag, False)
            target.save()

    def test_duplicate_or_invalid_club_data_preserves_original(self):
        self.client.force_login(self.users["OWNER"])
        before = self.snapshot()
        for changes in (
            {"club_name": self.other.club_name},
            {"club_name": ""},
            {"bank_account": "x" * 65},
        ):
            response = self.client.post(
                reverse("sport_club_modify_by_id", args=[self.club.pk]),
                self.club_data(**changes),
            )
            self.assertTrue(response.context["sportclubmodifyform"].errors)
            self.assertEqual(self.snapshot(), before)
        self.client.force_login(self.admin)
        before = self.snapshot()
        response = self.client.post(reverse("sport_club_add"), self.club_data())
        self.assertTrue(response.context["sportclubaddform"].errors)
        self.assertEqual(self.snapshot(), before)

    def test_inactive_recipient_cannot_receive_messages(self):
        self.client.force_login(self.users["OWNER"])
        ClubMembership.objects.filter(user=self.users["MEMBER"]).update(
            status="INACTIVE"
        )
        before = self.snapshot()
        url = reverse("send_message", args=[self.club.pk, self.people["MEMBER"].pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.post(
                url, {"message": "Rejected", "typeOfmessage": "InterStaff"}
            ).status_code,
            404,
        )
        self.assertEqual(self.snapshot(), before)

    def test_invalid_message_does_not_create_sender_profile(self):
        self.client.force_login(self.admin)
        before = self.snapshot()
        url = reverse("send_message", args=[self.club.pk, self.people["MEMBER"].pk])
        for data in (
            {"message": " ", "typeOfmessage": "InterStaff"},
            {"message": "Rejected", "typeOfmessage": "INVALID"},
            {"message": "Rejected"},
        ):
            response = self.client.post(url, data)
            self.assertTrue(response.context["messagesendform"].errors)
            self.assertEqual(self.snapshot(), before)

    def test_posted_sender_recipient_and_club_cannot_redirect_message(self):
        self.client.force_login(self.users["MEMBER"])
        response = self.client.post(
            reverse("send_message", args=[self.club.pk, self.people["COACH"].pk]),
            {
                "message": "Actual message",
                "typeOfmessage": "InterStaff",
                "from_who": self.foreign_person.pk,
                "to_who": self.foreign_person.pk,
                "sport_club": self.other.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        message = Table.objects.get()
        self.assertEqual(message.from_who, self.people["MEMBER"])
        self.assertEqual(message.to_who, self.people["COACH"])
        self.assertEqual(message.sport_club, self.club)

    def test_staff_with_model_permissions_cannot_use_platform_admin(self):
        user = self.users["MANAGER"]
        user.is_staff = True
        user.save()
        user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label="CrossBoxManager")
        )
        self.client.force_login(user)
        before = self.snapshot()
        for model, obj in (
            ("sportclub", self.club),
            ("clubmembership", ClubMembership.objects.get(user=user)),
        ):
            for name, args in (
                (f"admin:CrossBoxManager_{model}_changelist", []),
                (f"admin:CrossBoxManager_{model}_add", []),
                (f"admin:CrossBoxManager_{model}_change", [obj.pk]),
                (f"admin:CrossBoxManager_{model}_delete", [obj.pk]),
            ):
                with self.subTest(name=name):
                    self.assertEqual(
                        self.client.get(reverse(name, args=args)).status_code, 403
                    )
                    self.assertEqual(
                        self.client.post(
                            reverse(name, args=args), {"post": "yes"}
                        ).status_code,
                        403,
                    )
        self.assertEqual(self.snapshot(), before)


@override_settings(LOGIN_ACCOUNT_LIMIT=2, LOGIN_IP_LIMIT=3)
class NegativeLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="negative_login", password="Valid-password-861!"
        )

    def test_invalid_or_unknown_credentials_never_create_session(self):
        for data in (
            {},
            {"user_name": "negative_login"},
            {"user_name": "", "password": "password"},
            {"user_name": "missing_user", "password": "Valid-password-861!"},
            {"user_name": "negative_login", "password": "wrong"},
        ):
            response = self.client.post(reverse("login_page"), data)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(User.objects.count(), 1)

    def test_forged_forwarded_headers_do_not_bypass_ip_limit(self):
        for index in range(3):
            self.client.post(
                reverse("login_page"),
                {"user_name": f"missing_{index}", "password": "wrong"},
                REMOTE_ADDR="192.0.2.1",
                HTTP_X_FORWARDED_FOR=f"198.51.100.{index}",
            )
        self.client.post(
            reverse("login_page"),
            {"user_name": self.user.username, "password": "Valid-password-861!"},
            REMOTE_ADDR="192.0.2.1",
            HTTP_X_FORWARDED_FOR="203.0.113.5",
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(LoginAttempt.objects.count(), 4)

    def test_csrf_rejected_login_does_not_authenticate_or_consume_attempts(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("login_page"),
            {"user_name": self.user.username, "password": "Valid-password-861!"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", client.session)
        self.assertFalse(LoginAttempt.objects.exists())

    def test_deactivated_account_loses_existing_session_access(self):
        self.client.force_login(self.user)
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse("sport_clubs_show"))
        self.assertRedirects(
            response, reverse("login_page"), fetch_redirect_response=False
        )
