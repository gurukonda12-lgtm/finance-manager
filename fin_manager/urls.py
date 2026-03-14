from django.urls import path
from . import views
from .views import ExpenseListView
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('', views.home, name='home'),

    path('register/', views.register, name='register'),

    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    path('logout/', views.user_logout, name='logout'),

    path('expenses/', ExpenseListView.as_view(), name='expenses'),
]