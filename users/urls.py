from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_collection, name='user-collection'),       # GET y POST
    path('<int:pk>/', views.user_element, name='user-element'),    # GET, PUT y DELETE
]
