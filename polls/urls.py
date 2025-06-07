# polls/urls.py
from django.urls import path
from . import views

app_name = 'polls' # Це важливо для використання reverse()

urlpatterns = [
    path('', views.index, name='index'), # Стартова сторінка для введення нікнейму
    path('vote/', views.vote_view, name='vote'), # Сторінка голосування
    path('confirm/', views.confirm_vote, name='confirm_vote'), # Сторінка підтвердження голосування
    path('results/', views.results_view, name='results'), # Сторінка результатів
]