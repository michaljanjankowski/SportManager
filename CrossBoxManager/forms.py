from django import forms
from .models import WeekDays,Hours,MessageTypes, SportClub, Workers, Athletes, People, Table, TreningsHarmo, TreningEvent
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    user_name = forms.CharField(label="User Name", max_length=128)
    password = forms.CharField(label="Password", max_length=128, widget=forms.PasswordInput)

class SportClubAddForm(forms.ModelForm):
    class Meta:
        model = SportClub
        fields = ('club_name','address','nip','bank_account','founder','description')

class AthleteAddForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','password')
    isFeePayed = forms.BooleanField(label="Is Fee Payed ?",initial=False, required=False)


class WorkersAddForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email','password')
    is_manager = forms.BooleanField(label="Position Manager ?",initial=False, required=False)
    is_accountant = forms.BooleanField(label="Postion Accountant ?",initial=False, required=False)
    is_trener = forms.BooleanField(label="Position Coach ?",initial=False, required=False)


class AthleteModifyForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email')
    isFeePayed = forms.BooleanField(label="Is Fee Payed ?",initial=False, required=False)


class WorkersModifyForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','first_name','last_name','email')
    is_manager = forms.BooleanField(label="Position Manager ?",initial=False, required=False)
    is_accountant = forms.BooleanField(label="Postion Accountant ?",initial=False, required=False)
    is_trener = forms.BooleanField(label="Position Coach ?",initial=False, required=False)


class SendMessageForm(forms.ModelForm):

    class Meta:
        model = Table
        fields = ('message','typeOfmessage')

        widgets = {
                    'typeOfmessage': forms.Select(choices=MessageTypes, attrs={'class': 'form-control'}),
                  }