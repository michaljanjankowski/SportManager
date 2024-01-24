from django.contrib import admin
from .models import WeekDays,Hours,MessageTypes, SportClub, Workers, Athletes, People, Table, TreningsHarmo, TreningEvent

@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ['club_name','address','nip','bank_account','founder','description']



# Register your models here.
