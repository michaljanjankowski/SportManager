from django import forms
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
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import ClubMembership


class LoginForm(forms.Form):
    user_name = forms.CharField(label="User Name", max_length=128)
    password = forms.CharField(
        label="Password", max_length=128, widget=forms.PasswordInput
    )


class SportClubAddForm(forms.ModelForm):
    class Meta:
        model = SportClub
        fields = (
            "club_name",
            "address",
            "nip",
            "bank_account",
            "founder",
            "description",
        )


class PasswordValidationMixin:
    def clean(self):
        data = super().clean()
        if data.get("password"):
            user = User(
                **{
                    key: data.get(key, "")
                    for key in ("username", "first_name", "last_name", "email")
                }
            )
            try:
                validate_password(data["password"], user=user)
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return data


class AthleteAddForm(PasswordValidationMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    password = forms.CharField(
        label="Password", max_length=128, widget=forms.PasswordInput
    )
    isFeePayed = forms.BooleanField(
        label="Is Fee Payed ?", initial=False, required=False
    )


class WorkersAddForm(PasswordValidationMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    password = forms.CharField(
        label="Password", max_length=128, widget=forms.PasswordInput
    )
    role = forms.ChoiceField(choices=ClubMembership.Role.choices)


class AthleteModifyForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    isFeePayed = forms.BooleanField(
        label="Is Fee Payed ?", initial=False, required=False
    )


class WorkersModifyForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    role = forms.ChoiceField(choices=ClubMembership.Role.choices)


class SendMessageForm(forms.ModelForm):

    class Meta:
        model = Table
        fields = ("message", "typeOfmessage")

        widgets = {
            "typeOfmessage": forms.Select(
                choices=MessageTypes, attrs={"class": "form-control"}
            ),
        }
