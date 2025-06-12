# polls/urls.py
from django.urls import path
from . import views

app_name = 'polls' # Важливо, щоб простір імен був встановлений!

urlpatterns = [
    path('', views.index, name='index'),
    path('set_nickname/', views.set_nickname, name='set_nickname'),
    path('vote/', views.vote_view, name='vote'),
    path('confirm_vote/', views.confirm_vote, name='confirm_vote'),
    path('results/', views.results_view, name='results'),
    path('change_votes/', views.change_votes, name='change_votes'),
    # path('reset_all_votes/', views.reset_all_votes, name='reset_all_votes'), # Закоментовано, бо не має бути доступно користувачу
]