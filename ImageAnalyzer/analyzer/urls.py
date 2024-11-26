from django.urls import path
from analyzer import views


urlpatterns = [
    path('', views.index, name='index'),
]
