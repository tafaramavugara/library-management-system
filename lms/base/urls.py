from .views import *  
from django.urls import path

urlpatterns = [
    path('', Landing, name='stud_login'),
 
]
