from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/donate/', views.donate, name='donate'),
    path('projects/<int:project_id>/comment/', views.add_comment, name='add_comment'),
    path('projects/<int:project_id>/donations/', views.project_donations, name='project_donations'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('custom-admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/projects/', admin_views.admin_projects, name='admin_projects'),
    path('custom-admin/projects/<int:project_id>/edit/', admin_views.admin_edit_project, name='admin_edit_project'),
    path('custom-admin/projects/<int:project_id>/delete/', admin_views.admin_delete_project, name='admin_delete_project'),
    path('custom-admin/users/', admin_views.admin_users, name='admin_users'),
    path('custom-admin/users/<int:user_id>/delete/', admin_views.admin_delete_user, name='admin_delete_user'),
    path('custom-admin/donations/', admin_views.admin_donations, name='admin_donations'),
    path('custom-admin/donations/<int:donation_id>/delete/', admin_views.admin_delete_donation, name='admin_delete_donation'),
    path('custom-admin/comments/', admin_views.admin_comments, name='admin_comments'),
    path('custom-admin/comments/<int:comment_id>/delete/', admin_views.admin_delete_comment, name='admin_delete_comment'),
    path('custom-admin/settings/', admin_views.admin_settings, name='admin_settings'),
]
