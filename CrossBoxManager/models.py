from django.db import models
from django.contrib.auth.models import User

# Create your models here.

WeekDays = (
    ("", "Select training day"),
    ("Mon", "Monday"),
    ("Tue", "Tuesday"),
    ("Wed", "Wednesday"),
    ("Thu", "Thursday"),
    ("Fri", "Friday"),
    ("Sat", "Saturday"),
    ("Sun", "Sunday"),
)


Hours = (
    ("", "Select training hour"),
    (8, 8),
    (9, 9),
    (16, 16),
    (17, 17),
    (18, 18),
    (19, 19),
    (20, 20),
    (21, 21),
)

MessageTypes = (
    ("", "Select type of message"),
    ("InterStaff", "InterStaff"),
    ("InterToAthlete", "InterToAthlete"),
    ("StaffToAthlete", "StaffToAthlete"),
)


class SportClub(models.Model):
    club_name = models.CharField(max_length=64, unique=True)
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
    # TODO trening_plan ForiginKey to Trenings_Plans
    # TODO eating_plan ForeginKey to Eatings_Plan


# use Abstract User model
class People(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    worker = models.OneToOneField(Workers, null=True, on_delete=models.CASCADE)
    athlethe = models.OneToOneField(Athletes, null=True, on_delete=models.CASCADE)
    sport_club = models.ForeignKey(SportClub, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username


class Table(models.Model):
    from_who = models.ForeignKey(
        People, null=True, on_delete=models.SET_NULL, related_name="from_who"
    )
    to_who = models.ForeignKey(
        People, null=True, on_delete=models.SET_NULL, related_name="to_who"
    )
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
    trening_harmo = models.ForeignKey(
        TreningsHarmo, null=True, on_delete=models.SET_NULL
    )


# TODO
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


class ClubMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        COACH = "COACH", "Coach"
        MEMBER = "MEMBER", "Member"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="club_memberships"
    )
    club = models.ForeignKey(
        SportClub, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "club"], name="unique_club_membership"
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["OWNER", "MANAGER", "COACH", "MEMBER"]),
                name="valid_membership_role",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "INACTIVE"]),
                name="valid_membership_status",
            ),
        ]

    def __str__(self):
        return f"{self.user} / {self.club} / {self.role}"


class LoginAttempt(models.Model):
    # Shared database counters work across processes and include admin login.
    key = models.CharField(max_length=64, unique=True)
    started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)
