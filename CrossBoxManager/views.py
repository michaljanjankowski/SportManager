from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.http import HttpResponse, request
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .models import WeekDays,Hours,MessageTypes, SportClub, Workers, Athletes, People, Table, TreningsHarmo, TreningEvent
from .forms import LoginForm, SportClubAddForm, AthleteAddForm, WorkersAddForm, AthleteModifyForm, WorkersModifyForm, SendMessageForm
import time
import datetime

# Create your views here.

class LoginView(View):
    def get(self, request):
        loginform = LoginForm()
        return render(request,"login_page.html",{'loginform':loginform})

    def post(self, request):
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            #Note: after is_valid() cleaned_data can be used
            username = loginform.cleaned_data['user_name']
            password = loginform.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('sport_clubs_show')
            else:
                error_message = "Wrong credentials"
                return render(request, "loginform.html", {"loginform": loginform, "error_message": error_message})
        else:
            error_message = "Wrong credentials. Form not valid"
            return render(request, "loginform.html", {"loginform": loginform, "error_message": error_message})


class SportClubsShowView(View):
    def get(self, request):
        clubs = SportClub.objects.all()
        return render(request,"all_sport_clubs.html",{'clubs':clubs})

class SportClubAddView(View):
    def get(self, request):
        sportclubaddform = SportClubAddForm()
        return render(request,"sport_club_add.html",{'sportclubaddform':sportclubaddform})

    def post(self, request):
        sportclubaddform = SportClubAddForm(request.POST)
        if sportclubaddform.is_valid():
            sportclubaddform.save()
            return redirect('sport_clubs_show')
        else:
            return HttpResponse("Invalid Product Data")

class SportClubEnterView(View):
    def get(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        return render(request,'enter_club.html',{'club':club})

    def post(self, request):
        pass


class SportClubModifyView(View):
    def get(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        sportclubform = SportClubAddForm(instance=club)
        return render(request, 'sport_club_modify.html', {'club': club, 'sportclubmodifyform':sportclubform})

    def post(self, request, sport_club_id ):
        club = SportClub.objects.get(id=sport_club_id)
        sportclubform = SportClubAddForm(request.POST, instance=club)
        if sportclubform.is_valid():
            #is_valid() does it checks if club_name is uniqe?
            club.club_name = sportclubform.cleaned_data['club_name']
            club.address = sportclubform.cleaned_data['address']
            club.nip = sportclubform.cleaned_data['nip']
            club.bank_account = sportclubform.cleaned_data['bank_account']
            club.founder = sportclubform.cleaned_data['founder']
            club.description = sportclubform.cleaned_data['description']
            try:
                club.save()
            except:
                return HttpResponse('Sport club name already used.')
            return redirect('sport_clubs_show')
        else:
            return HttpResponse('Club Modify form not valid')


class PeopleShowView(View):
    "By ClubId"
    def get(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        try:
            people = People.objects.all().filter(sport_club=sport_club_id)
            peoplelist = []
            for person in people:
                person_id = person.id
                username = person.user.username
                first_name = person.user.first_name
                last_name = person.user.last_name
                email = person.user.email
                if person.worker != None and person.athlethe == None:
                    #print('Person is worker')
                    is_manager = person.worker.is_manager
                    is_accountant = person.worker.is_accountant
                    is_trener = person.worker.is_trener
                    is_fee_payed = False

                if person.worker == None and person.athlethe != None:
                    #print('Person is athlete')
                    is_manager = False
                    is_accountant = False
                    is_trener = False
                    is_fee_payed = person.athlethe.isFeePayed

                if person.worker != None and person.athlethe != None:
                    #print('person is worker and athelete')
                    is_manager = person.worker.is_manager
                    is_accountant = person.worker.is_accountant
                    is_trener = person.worker.is_trener
                    is_fee_payed = person.athlethe.isFeePayed

                peoplelist.append((
                 person_id,
                 username,
                 first_name,
                 last_name,
                 email,
                 is_manager,
                 is_accountant,
                 is_trener,
                 is_fee_payed
                ))

            #print(peoplelist)
            error_message =''
            #will throw exeption, when People table is empty
        except People.DoesNotExist:
            people = None
            error_message = "There are no people in sport club {}".format(club.club_name)
        return render(request, 'all_people_show.html',
                          {'people': peoplelist, 'club': club, 'error_message': error_message})


class AthleteAddView(View):
    "By ClubId"
    def get(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        personaddform = AthleteAddForm()
        return render(request, 'athlete_add.html', {'club':club,'personaddform':personaddform})

    def post(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        personaddform = AthleteAddForm(request.POST)
        if personaddform.is_valid():
            username = personaddform.cleaned_data['username']
            checkuser = User.objects.filter(username=username)
            if len(checkuser) > 0:
                error_message = "Wrong credentials, user already exists"
                return render(request, 'athlete_add.html',
                              {'club': club, 'personaddform': personaddform, 'error_message':error_message})
            password = personaddform.cleaned_data['password']
            first_name = personaddform.cleaned_data['first_name']
            last_name = personaddform.cleaned_data['last_name']
            email = personaddform.cleaned_data['email']
            isFee = personaddform.cleaned_data['isFeePayed']
            People.objects.create(
                user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name,last_name=last_name),
                athlethe = Athletes.objects.create(isFeePayed=isFee),
                sport_club = club
            )
            error_message = "Athlete added"
            return render(request, 'athlete_add.html',
                          {'club': club, 'personaddform': personaddform, 'error_message': error_message})
        else:
            error_message = "Credetials not valid"
            return render(request, 'athlete_add.html',
                          {'club': club, 'personaddform': personaddform, 'error_message': error_message})

class WorkerAddView(View):
    "By ClubId"
    def get(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        personaddform = WorkersAddForm()
        return render(request, 'worker_add.html', {'club':club,'personaddform':personaddform})

    def post(self, request, sport_club_id):
        club = SportClub.objects.get(id=sport_club_id)
        personaddform = WorkersAddForm(request.POST)
        if personaddform.is_valid():
            username = personaddform.cleaned_data['username']
            checkuser = User.objects.filter(username=username)
            if len(checkuser) > 0:
                error_message = "Wrong credentials, user already exists"
                return render(request, 'athlete_add.html',
                              {'club': club, 'personaddform': personaddform, 'error_message': error_message})
            password = personaddform.cleaned_data['password']
            first_name = personaddform.cleaned_data['first_name']
            last_name = personaddform.cleaned_data['last_name']
            email = personaddform.cleaned_data['email']
            is_manager = personaddform.cleaned_data['is_manager']
            is_accountant = personaddform.cleaned_data['is_accountant']
            is_trener = personaddform.cleaned_data['is_trener']
            People.objects.create(
                user=User.objects.create_user(username=username, email=email, password=password, first_name=first_name,
                                              last_name=last_name),
                worker=Workers.objects.create(is_manager=is_manager,
                                                is_accountant=is_accountant,
                                                is_trener=is_trener),
                sport_club=club
            )
            error_message = "Worker added"
            return render(request, 'athlete_add.html',
                          {'club': club, 'personaddform': personaddform, 'error_message': error_message})
        else:
            error_message = "Credetials not valid"
            return render(request, 'athlete_add.html',
                          {'club': club, 'personaddform': personaddform, 'error_message': error_message})

class PersonModifyView(View):
    "By ClubId and peopleId"
    def get(self, request, sport_club_id, people_id ):
        club = SportClub.objects.get(id=sport_club_id)
        person = People.objects.get(id=people_id)
        if person.worker != None and person.athlethe == None:
            print('worker modyfication')
            workerform = WorkersModifyForm(initial={
                                        'username' : person.user.username,
                                        'first_name': person.user.first_name,
                                         'last_name': person.user.last_name,
                                         'email':person.user.email,
                                         'is_manager':person.worker.is_manager,
                                         'is_accountant':person.worker.is_accountant,
                                         'is_trener':person.worker.is_trener
                                        })
            personmodyfieform = workerform
        if person.worker == None and person.athlethe != None:
            print('athethe modyfication')
            athletheform = AthleteModifyForm(initial={
                                        'username': person.user.username,
                                        'first_name': person.user.first_name,
                                        'last_name': person.user.last_name,
                                         'email': person.user.email,
                                         'isFeePayed':person.athlethe.isFeePayed
            })
            personmodyfieform = athletheform
        return render(request, 'person_modyfie.html',
                      {'club':club,'personmodyfieform':personmodyfieform,'person':person})

    def post(self, request, sport_club_id, people_id):
        club = SportClub.objects.get(id=sport_club_id)
        person = People.objects.get(id=people_id)
        if person.worker != None and person.athlethe == None:
            # worker
            workerform = WorkersModifyForm(request.POST, instance=person)
            if workerform.is_valid():
                # is_valid() does it checks if club_name is uniqe?
                # I need modify username to modify person
                # or use instance = person
                person.user.username = workerform.cleaned_data['username']
                person.user.first_name = workerform.cleaned_data['first_name']
                person.user.last_name = workerform.cleaned_data['last_name']
                person.user.email = workerform.cleaned_data['email']
                person.worker.is_manager = workerform.cleaned_data['is_manager']
                person.worker.is_accountant = workerform.cleaned_data['is_accountant']
                person.worker.is_trener = workerform.cleaned_data['is_trener']
                person.user.save()
                person.worker.save()
            else:
                return HttpResponse('Worker modyfie form not valid')


        if person.worker == None and person.athlethe != None:
            # athlethe
            athletheform = AthleteModifyForm(request.POST, instance=person)
            if athletheform.is_valid():
                # is_valid() does it checks if club_name is uniqe?
                # I need modify username to modify person
                # or use instance = person
                person.user.username = athletheform.cleaned_data['username']
                person.user.first_name = athletheform.cleaned_data['first_name']
                person.user.last_name = athletheform.cleaned_data['last_name']
                person.user.email = athletheform.cleaned_data['email']
                person.athlethe.isFeePayed = athletheform.cleaned_data['isFeePayed']
                person.user.save()
                person.athlethe.save()
            else:
                return HttpResponse('Athethe modyfie form not valid')

        return redirect('people_show_by_club_id',sport_club_id=club.id)


class MessagesToPersonView(View):
    "By ClubId and by person id"
    def get(self, request, sport_club_id, people_id):
        pass

    def post(self, request, sport_club_id, people_id):
        pass

class MessagesinClubShowView(View):
    "By ClubId"
    pass


# class Table(models.Model):
#     from_who = models.ForeignKey(People,  null=True, on_delete=models.SET_NULL, related_name="from_who")
#     to_who = models.ForeignKey(People, null=True, on_delete=models.SET_NULL, related_name="to_who")
#     message = models.TextField()
#     date_posted = models.DateTimeField()
#     typeOfmessage = models.CharField(max_length=128, choices=MessageTypes)
#     sport_club = models.ForeignKey(SportClub, null=True, on_delete=models.SET_NULL)


class MessageSendView(View):
    "By ClubId and PersonId"

    def get(self, request, sport_club_id, people_id):
        club = SportClub.objects.get(id=sport_club_id)
        messagesendform = SendMessageForm()
        receiving_person = People.objects.get(id=people_id)
        user=User.objects.get(username=request.user.username)
        sending_person = People.objects.get(user=user.id)
        date = datetime.datetime.now()
        return render(request, 'send_messge_from_person_to_person.html',
                      {'club': club,
                       'messagesendform': messagesendform,
                       'receiving_person': receiving_person,
                       'sending_person':sending_person,
                       'date':date})

    def post(self, request, sport_club_id, people_id):
        club = SportClub.objects.get(id=sport_club_id)
        messagesendform = SendMessageForm(request.POST)
        if messagesendform.is_valid():
            receiving_person = People.objects.get(id=people_id)
            user = User.objects.get(username=request.user.username)
            sending_person = People.objects.get(user=user.id)
            date = datetime.datetime.now()
            Table.objects.create(
                from_who = sending_person,
                to_who = receiving_person,
                message = messagesendform.cleaned_data['message'],
                typeOfmessage = messagesendform.cleaned_data['typeOfmessage'],
                date_posted = date,
                sport_club = club
            )
        else:
            return HttpResponse('Message form not valid')
        return redirect('people_show_by_club_id', sport_club_id=club.id)

#Most problably will not be used in this milestone
class TreningsHarmoShowView(View):
    pass

class TrenigsHarmoAddView(View):
    pass

class TrenigsHarmoModifyView(View):
    pass