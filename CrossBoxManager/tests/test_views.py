from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from ..models import Athletes, People, SportClub, Table, ClubMembership


class ClubDetailsTests(TestCase):
    def setUp(self):
        self.club = SportClub.objects.create(
            club_name="Test club",
            address="Test address",
            nip="123",
            bank_account="123",
            founder="Founder",
            description="Description",
        )
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.url = reverse("sport_club_details_by_id", args=[self.club.pk])

    def test_superuser_without_people_profile_can_open_club(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, self.club.club_name)
        self.assertEqual(response.context["parent_club"], "User not asigned to club")

    def test_user_without_assigned_club_can_open_club(self):
        People.objects.create(user=self.user, athlethe=Athletes.objects.create())
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["parent_club"], "User not asigned to club")

    def test_user_with_club_profile_can_open_club(self):
        People.objects.create(
            user=self.user,
            sport_club=self.club,
            athlethe=Athletes.objects.create(),
        )
        ClubMembership.objects.create(user=self.user, club=self.club)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, self.club.club_name)
        self.assertEqual(response.context["parent_club"], self.club.club_name)

    def test_missing_or_invalid_club_returns_404(self):
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(
                reverse(
                    "sport_club_details_by_id",
                    args=[self.club.pk + 1],
                )
            ).status_code,
            404,
        )
        self.assertEqual(self.client.get("/club_enter/invalid").status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)


class PersonalMessagesTests(TestCase):
    def setUp(self):
        self.club = SportClub.objects.create(
            club_name="Inbox club",
            address="Address",
            nip="123",
            bank_account="123",
            founder="Founder",
            description="Description",
        )
        self.user = User.objects.create_user(username="recipient")
        self.url = reverse("msg_show_to_person", args=[self.club.pk])

    def test_account_without_profile_has_no_inbox(self):
        self.user.is_superuser = True
        self.user.save()
        Table.objects.create(
            sport_club=self.club,
            to_who=None,
            message="Unassigned private message",
            date_posted=timezone.now(),
            typeOfmessage="InterStaff",
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Your account is not assigned to this club")
        self.assertNotContains(response, "Unassigned private message")
        self.assertEqual(list(response.context["messages"]), [])

    def test_inbox_only_shows_own_messages_in_requested_club(self):
        person = People.objects.create(
            user=self.user,
            sport_club=self.club,
            athlethe=Athletes.objects.create(),
        )
        other_club = SportClub.objects.create(
            club_name="Other club",
            address="Address",
            nip="456",
            bank_account="456",
            founder="Founder",
            description="Description",
        )
        for club, recipient, content in [
            (self.club, person, "Own private message"),
            (self.club, None, "Someone else's message"),
            (other_club, person, "Message in another club"),
        ]:
            Table.objects.create(
                sport_club=club,
                to_who=recipient,
                message=content,
                date_posted=timezone.now(),
                typeOfmessage="InterStaff",
            )
        ClubMembership.objects.create(user=self.user, club=self.club)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Own private message")
        self.assertNotContains(response, "Someone else's message")
        self.assertNotContains(response, "Message in another club")
        response = self.client.get(reverse("msg_show_to_person", args=[other_club.pk]))
        self.assertEqual(response.status_code, 403)

    def test_empty_inbox(self):
        People.objects.create(
            user=self.user,
            sport_club=self.club,
            athlethe=Athletes.objects.create(),
        )
        self.client.force_login(self.user)
        ClubMembership.objects.create(user=self.user, club=self.club)
        self.assertContains(
            self.client.get(self.url), "You have no messages in this club"
        )

    def test_missing_club_returns_404(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("msg_show_to_person", args=[self.club.pk + 1])
        )
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)


class MessageSendingTests(TestCase):
    def setUp(self):
        self.club = SportClub.objects.create(
            club_name="Messaging",
            address="Address",
            nip="123",
            bank_account="123",
            founder="Founder",
            description="Description",
        )
        self.admin = User.objects.create_superuser(
            username="sender_admin",
            email="admin@example.com",
            password="password",
        )
        self.recipient = People.objects.create(
            user=User.objects.create_user(username="message_recipient"),
            sport_club=self.club,
        )
        ClubMembership.objects.create(user=self.recipient.user, club=self.club)
        self.url = reverse("send_message", args=[self.club.pk, self.recipient.pk])
        self.data = {"message": "Hello from admin", "typeOfmessage": "InterStaff"}

    def test_superuser_without_profile_can_open_and_send(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(self.url), self.admin.username)
        self.assertFalse(People.objects.filter(user=self.admin).exists())
        self.assertEqual(self.client.post(self.url, self.data).status_code, 302)
        message = Table.objects.get()
        self.assertEqual(message.from_who.user, self.admin)
        self.assertIsNone(message.from_who.sport_club_id)
        self.assertEqual(message.to_who, self.recipient)
        self.assertEqual(message.sport_club, self.club)

    def test_invalid_form_does_not_create_profile_or_message(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {"message": "", "typeOfmessage": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["messagesendform"].errors)
        self.assertFalse(Table.objects.exists())
        self.assertFalse(People.objects.filter(user=self.admin).exists())

    def test_recipient_must_belong_to_selected_club(self):
        self.client.force_login(self.admin)
        ClubMembership.objects.filter(user=self.recipient.user).delete()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 404)
        self.assertFalse(Table.objects.exists())

    def test_regular_member_can_send_but_unassigned_user_cannot(self):
        user = User.objects.create_user(username="regular_sender")
        self.client.force_login(user)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 403)
        People.objects.create(user=user, sport_club=self.club)
        ClubMembership.objects.create(user=user, club=self.club)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 302)
        self.assertEqual(Table.objects.get().from_who.user, user)

    def test_anonymous_user_is_redirected(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 302)
        self.assertFalse(Table.objects.exists())
