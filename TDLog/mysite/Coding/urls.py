from django.urls import path
from . import views

app_name = 'coding'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('initial-test/', views.take_initial_test, name='initial_test'),
    path('problems/', views.problems_view, name='problems'),
    path('api/problems/<int:domain_id>/', views.get_domain_problems, name='get_domain_problems'),
    path('submit-initial-test/', views.submit_initial_test, name='submit_initial_test'),
    path('complete-initial-test/', views.complete_initial_test, name='complete_initial_test'),
    path('problem/<int:problem_id>/', views.problem_detail, name='problem_detail'),
    path('problem/<int:problem_id>/submit/', views.submit_solution, name='submit_solution'),
    path('problem/<int:problem_id>/test/', views.test_solution, name='test_solution'),
    path('problem/<int:problem_id>/give-up/', views.give_up_problem, name='give_up_problem'),
]