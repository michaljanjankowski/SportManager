from django.db import models
from django.contrib.auth.models import User

# Create your models here.

WeekDays = (
    ("Mon","Monday"),
    ("Tue", "Tuesday"),
    ("Wed", "Wednesday"),
    ("Thu", "Thursday"),
    ("Fri","Friday"),
    ("Sat","Saturday"),
    ("Sun","Sunday"),
)


Hours = (
    (8,8),
    (9,9),
    (16,16),
    (17,17),
    (18,18),
    (19,19),
    (20,20),
    (21,21),
)

MessageTypes =(
    ("InterStaff","InterStaff"),
    ("InterAthlete","InterAthlete"),
    ("StaffAthlete","StaffAthlete"),
)


class SportClub(models.Model):
    club_name = models.CharField(max_length=64,unique=True)
    address = models.CharField(max_length=128)
    nip = models.CharField(max_length=64)
    bank_account = models.CharField(max_length=64)
    founder = models.CharField(max_length=128)
    description = models.TextField()

    def __str__(self):
        return self.club_name


class Workers(models.Model):
    is_manager = models.BooleanField(default=False)
    is_accountant = models.BooleanField(default=False)
    is_trener = models.BooleanField(default=True)

class Athletes(models.Model):
    isFeePayed = models.BooleanField(default=False)
    #TODO trening_plan ForiginKey to Trenings_Plans
    #TODO eating_plan ForeginKey to Eatings_Plan

#use Abstract User model
class People(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    worker = models.OneToOneField(Workers, null=True, on_delete=models.CASCADE)
    athlethe = models.OneToOneField(Athletes, null=True, on_delete=models.CASCADE)
    sport_club = models.ForeignKey(SportClub, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username

class Table(models.Model):
    from_who = models.ForeignKey(People,  null=True, on_delete=models.SET_NULL, related_name="from_who")
    to_who = models.ForeignKey(People, null=True, on_delete=models.SET_NULL, related_name="to_who")
    message = models.TextField()
    date_posted = models.DateTimeField()
    typeOfmessage = models.CharField(max_length=128, choices=MessageTypes)
    sport_club = models.ForeignKey(SportClub, null=True, on_delete=models.SET_NULL)

class TreningsHarmo(models.Model):
    trening_name = models.CharField(max_length=64)
    leading_trainer = models.CharField(max_length=64)
    week_day = models.CharField(max_length=128, choices=WeekDays)
    hour = models.TimeField(choices=Hours)
    sport_club = models.ForeignKey(SportClub, null=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField(People, through="TreningEvent")

class TreningEvent(models.Model):
    trening_program = models.TextField()
    date = models.DateTimeField()
    members = models.ForeignKey(People, null=True, on_delete=models.SET_NULL)
    trening_harmo = models.ForeignKey(TreningsHarmo, null=True, on_delete=models.SET_NULL)

#TODO
# class Room(models.Model):
#     room_name = models.CharField(max_length=64,unique=True)
#     room_capacity = models.IntegerField()
#     box = models.ForeignKey(CrossBox, on_delete=models.CASCADE)
#
# class Equipment(models.Model):
#     equpment_name = models.CharField(max_length=64,unique=True)
#     amount = models.IntegerField()
#     box = models.ForeignKey(CrossBox, on_delete=models.SET_NULL)

# class Trenings_Plans(models.Model):
#   pass
