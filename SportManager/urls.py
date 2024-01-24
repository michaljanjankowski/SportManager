"""SportManager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from CrossBoxManager.views import SportClubsShowView, SportClubAddView,SportClubEnterView, SportClubModifyView, PeopleShowView, \
    PersonModifyView, MessagesinClubShowView, MessagesToPersonView, MessageSendView, TreningsHarmoShowView, TrenigsHarmoAddView, TrenigsHarmoModifyView, \
    AthleteAddView, WorkerAddView, LoginView, LogoutView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login_page'),
    path('logout/', LogoutView.as_view(),name='logout_page'),
    path('clubs/', SportClubsShowView.as_view(), name='sport_clubs_show'),
    path('club_add/',SportClubAddView.as_view(), name='sport_club_add'),
    path('club_enter/<sport_club_id>',SportClubEnterView.as_view(), name='sport_club_details_by_id'),
    path('club_modify/<sport_club_id>',SportClubModifyView.as_view(),name='sport_club_modify_by_id'),

    path('people/<sport_club_id>',PeopleShowView.as_view(),name='people_show_by_club_id'),
    path('athlete_add/<sport_club_id>/', AthleteAddView.as_view(), name='athlete_add_by_club_id'),
    path('worker_add/<sport_club_id>/', WorkerAddView.as_view(), name='worker_add_by_club_id'),
    path('person_show/<sport_club_id>/<people_id>',PeopleShowView.as_view(), name='person_details_by_club_id'),
    path('person_modify/<sport_club_id>/<people_id>', PersonModifyView.as_view(), name='person_in_club_modify_by_id'),

    path('msgshow_toperson/<sport_club_id>/', MessagesToPersonView.as_view(), name='msg_show_to_person'),
    path('message_add/<sport_club_id>/<people_id>',MessageSendView.as_view(),name='send_message'), #(send)add message in sport club to given person

    #TODO
    path('message_show/<sport_club_id>', MessagesinClubShowView.as_view(), name='all_messages_in_club_show'), #show all messages in sport club

]
