from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from .forms import (
    LoginForm,
    SportClubAddForm,
    AthleteAddForm,
    WorkersAddForm,
    AthleteModifyForm,
    WorkersModifyForm,
    SendMessageForm,
)
from .models import SportClub, People, Workers, Athletes, Table, ClubMembership
from .permissions import ClubAccessMixin, ClubManagementMixin, SuperuserMixin, can_edit_person


class LoginView(View):
    def get(self, request):
        return render(request, "login_page.html", {"loginform": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["user_name"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("sport_clubs_show")
        return render(
            request,
            "login_page.html",
            {
                "loginform": form,
                "error_message": "Wrong credentials or too many login attempts. Try again later.",
            },
        )


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect("login_page")


class SportClubsShowView(LoginRequiredMixin, View):
    def get(self, request):
        clubs = (
            SportClub.objects.all()
            if request.user.is_superuser
            else SportClub.objects.filter(
                memberships__user=request.user,
                memberships__status=ClubMembership.Status.ACTIVE,
            )
        )
        return render(request, "all_sport_clubs.html", {"clubs": clubs})


class SportClubAddView(SuperuserMixin, View):
    def get(self, request):
        return render(
            request, "sport_club_add.html", {"sportclubaddform": SportClubAddForm()}
        )

    @transaction.atomic
    def post(self, request):
        form = SportClubAddForm(request.POST)
        if form.is_valid():
            club = form.save()
            ClubMembership.objects.create(
                user=request.user, club=club, role=ClubMembership.Role.OWNER
            )
            return redirect("sport_clubs_show")
        return render(request, "sport_club_add.html", {"sportclubaddform": form})


class SportClubEnterView(ClubAccessMixin, View):
    def get(self, request, sport_club_id):
        return render(request, "enter_club.html", {"club": self.club})


class SportClubModifyView(ClubManagementMixin, View):
    def get(self, request, sport_club_id):
        return self.render_form(request, SportClubAddForm(instance=self.club))

    def render_form(self, request, form):
        return render(
            request,
            "sport_club_modify.html",
            {"club": self.club, "sportclubmodifyform": form},
        )

    def post(self, request, sport_club_id):
        form = SportClubAddForm(request.POST, instance=self.club)
        if form.is_valid():
            form.save()
            return redirect("sport_clubs_show")
        return self.render_form(request, form)


class PeopleShowView(ClubAccessMixin, View):
    allowed_roles = (
        ClubMembership.Role.OWNER,
        ClubMembership.Role.MANAGER,
        ClubMembership.Role.COACH,
    )

    def get(self, request, sport_club_id, people_id=None):
        people = People.objects.filter(
            user__club_memberships__club=self.club,
            user__club_memberships__status=ClubMembership.Status.ACTIVE,
        ).select_related("user", "athlethe").prefetch_related("user__club_memberships")
        if people_id is not None:
            people = people.filter(pk=people_id)
            get_object_or_404(people)
        roles = dict(self.club.memberships.values_list("user_id", "role"))
        rows = [
            (
                p.pk,
                p.user.username,
                p.user.first_name,
                p.user.last_name,
                p.user.email,
                roles[p.user_id] in ("OWNER", "MANAGER"),
                False,
                roles[p.user_id] == "COACH",
                p.athlethe.isFeePayed if p.athlethe_id else False,
                can_edit_person(request.user, self.membership, p, roles[p.user_id]),
            )
            for p in people
        ]
        return render(
            request, "all_people_show.html", {"club": self.club, "people": rows}
        )


def staff_choices(user, membership):
    # Managers can add coaches, but cannot create peers or owners.
    if user.is_superuser or membership.role == ClubMembership.Role.OWNER:
        return ClubMembership.Role.choices
    return [
        (ClubMembership.Role.COACH, "Coach"),
        (ClubMembership.Role.MEMBER, "Member"),
    ]


class AthleteAddView(ClubManagementMixin, View):
    form_class = AthleteAddForm
    template_name = "athlete_add.html"
    staff = False

    def get_form(self, request, data=None):
        form = self.form_class(data)
        if self.staff:
            form.fields["role"].choices = staff_choices(request.user, self.membership)
        return form

    def render_form(self, request, form, message=""):
        return render(
            request,
            self.template_name,
            {"club": self.club, "personaddform": form, "error_message": message},
        )

    def get(self, request, sport_club_id):
        return self.render_form(request, self.get_form(request))

    @transaction.atomic
    def post(self, request, sport_club_id):
        form = self.get_form(request, request.POST)
        if not form.is_valid():
            return self.render_form(request, form)
        data = form.cleaned_data
        user = User.objects.create_user(
            **{
                k: data[k]
                for k in ("username", "password", "first_name", "last_name", "email")
            }
        )
        profile = People(user=user, sport_club=self.club)
        role = data["role"] if self.staff else ClubMembership.Role.MEMBER
        if self.staff:
            # Legacy profile data is retained; flags no longer authorize operations.
            profile.worker = Workers.objects.create(is_trener=role == "COACH")
        else:
            profile.athlethe = Athletes.objects.create(isFeePayed=data["isFeePayed"])
        profile.save()
        ClubMembership.objects.create(user=user, club=self.club, role=role)
        return self.render_form(request, self.get_form(request), "Person added")


class WorkerAddView(AthleteAddView):
    form_class = WorkersAddForm
    template_name = "worker_add.html"
    staff = True


class PersonModifyView(ClubManagementMixin, View):
    def target(self, request, people_id):
        person = get_object_or_404(
            People, pk=people_id, user__club_memberships__club=self.club
        )
        membership = get_object_or_404(ClubMembership, user=person.user, club=self.club)
        if not can_edit_person(request.user, self.membership, person, membership.role):
            raise PermissionDenied
        return person, membership

    def form(self, request, person, membership, data=None):
        cls = WorkersModifyForm if person.worker_id else AthleteModifyForm
        form = cls(
            data,
            instance=person.user,
            initial={
                "role": membership.role,
                "isFeePayed": (
                    person.athlethe.isFeePayed if person.athlethe_id else False
                ),
            },
        )
        if "role" in form.fields:
            form.fields["role"].choices = staff_choices(request.user, self.membership)
        return form

    def render_form(self, request, person, form):
        return render(
            request,
            "person_modyfie.html",
            {"club": self.club, "person": person, "personmodyfieform": form},
        )

    def get(self, request, sport_club_id, people_id):
        person, membership = self.target(request, people_id)
        return self.render_form(request, person, self.form(request, person, membership))

    @transaction.atomic
    def post(self, request, sport_club_id, people_id):
        person, membership = self.target(request, people_id)
        form = self.form(request, person, membership, request.POST)
        if not form.is_valid():
            return self.render_form(request, person, form)
        # Owner memberships can only be changed through the platform admin.
        new_role = form.cleaned_data.get("role", membership.role)
        if (
            membership.role == "OWNER"
            and new_role != "OWNER"
            and not request.user.is_superuser
        ):
            raise PermissionDenied
        form.save()
        membership.role = new_role
        membership.save(update_fields=["role"])
        if person.athlethe_id:
            person.athlethe.isFeePayed = form.cleaned_data.get(
                "isFeePayed", person.athlethe.isFeePayed
            )
            person.athlethe.save(update_fields=["isFeePayed"])
        return redirect("people_show_by_club_id", sport_club_id=self.club.pk)


class MessagesToPersonView(ClubAccessMixin, View):
    def get(self, request, sport_club_id):
        person = People.objects.filter(user=request.user).first()
        messages = (
            Table.objects.filter(to_who=person, sport_club=self.club)
            if person
            else Table.objects.none()
        )
        return render(
            request,
            "receive_messages_for_given_person.html",
            {
                "club": self.club,
                "messages": messages,
                "has_club_profile": person is not None,
            },
        )


class MessageSendView(ClubAccessMixin, View):
    def recipient(self, people_id):
        return get_object_or_404(
            People,
            pk=people_id,
            user__club_memberships__club=self.club,
            user__club_memberships__status=ClubMembership.Status.ACTIVE,
        )

    def render_form(self, request, form, recipient):
        return render(
            request,
            "send_messge_from_person_to_person.html",
            {
                "club": self.club,
                "messagesendform": form,
                "receiving_person": recipient,
                "sending_user": request.user,
                "date": timezone.now(),
            },
        )

    def get(self, request, sport_club_id, people_id):
        return self.render_form(request, SendMessageForm(), self.recipient(people_id))

    @transaction.atomic
    def post(self, request, sport_club_id, people_id):
        recipient = self.recipient(people_id)
        form = SendMessageForm(request.POST)
        if not form.is_valid():
            return self.render_form(request, form, recipient)
        sender, _ = People.objects.get_or_create(user=request.user)
        Table.objects.create(
            from_who=sender,
            to_who=recipient,
            sport_club=self.club,
            date_posted=timezone.now(),
            **form.cleaned_data,
        )
        return redirect("msg_show_to_person", sport_club_id=self.club.pk)


class MessagesinClubShowView(ClubManagementMixin, View):
    def get(self, request, sport_club_id):
        return HttpResponse("Club message board is not available", status=501)


class TreningsHarmoShowView(ClubAccessMixin, View):
    pass


class TrenigsHarmoAddView(ClubManagementMixin, View):
    pass


class TrenigsHarmoModifyView(ClubManagementMixin, View):
    pass
