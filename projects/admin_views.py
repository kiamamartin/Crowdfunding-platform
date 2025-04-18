from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Project, Donation, Comment
from .forms import ProjectForm
import json
from datetime import datetime, timedelta
from calendar import month_name

# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard view showing overview statistics and recent activities"""
    # Get statistics
    total_projects = Project.objects.count()
    total_users = User.objects.count()
    total_donations = Donation.objects.count()
    total_funding = Donation.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get recent projects and donations
    recent_projects = Project.objects.order_by('-created_at')[:5]
    recent_donations = Donation.objects.order_by('-donated_at')[:5]
    
    # Calculate progress for each project
    for project in recent_projects:
        project.progress = int((project.current_amount / project.goal_amount) * 100)
        project.days_left = (project.deadline - timezone.now().date()).days
    
    # Generate monthly funding data for chart
    months_data = []
    monthly_funding = []
    
    # Get data for the last 6 months
    today = timezone.now().date()
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        month_name_str = month_start.strftime("%b")
        months_data.append(month_name_str)
        
        month_funding = Donation.objects.filter(
            donated_at__date__gte=month_start,
            donated_at__date__lte=month_end
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_funding.append(float(month_funding))
    
    context = {
        'active_tab': 'dashboard',
        'total_projects': total_projects,
        'total_users': total_users,
        'total_donations': total_donations,
        'total_funding': total_funding,
        'recent_projects': recent_projects,
        'recent_donations': recent_donations,
        'months': json.dumps(months_data),
        'monthly_funding': json.dumps(monthly_funding),
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_projects(request):
    """Admin view to manage all projects"""
    projects = Project.objects.all().order_by('-created_at')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(title__icontains=search_query)
    
    # Calculate progress and days left for each project
    for project in projects:
        project.progress = int((project.current_amount / project.goal_amount) * 100)
        project.days_left = (project.deadline - timezone.now().date()).days
    
    # Pagination
    paginator = Paginator(projects, 10)  # Show 10 projects per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_tab': 'projects',
        'projects': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'admin/projects.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_project(request, project_id):
    """Admin view to edit a project"""
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.title}" updated successfully!')
            return redirect('admin_projects')
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'active_tab': 'projects',
        'form': form,
        'project': project,
    }
    
    return render(request, 'admin/edit_project.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_project(request, project_id):
    """Admin view to delete a project"""
    project = get_object_or_404(Project, id=project_id)
    project_title = project.title
    project.delete()
    messages.success(request, f'Project "{project_title}" deleted successfully!')
    return redirect('admin_projects')

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Admin view to manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(username__icontains=search_query) | users.filter(email__icontains=search_query)
    
    # Add project and donation counts for each user
    for user in users:
        user.projects_count = Project.objects.filter(creator=user).count()
        user.donations_count = Donation.objects.filter(donor=user).count()
        user.donations_amount = Donation.objects.filter(donor=user).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_tab': 'users',
        'users': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    """Admin view to delete a user"""
    user = get_object_or_404(User, id=user_id)
    
    # Don't allow deleting superusers
    if user.is_superuser:
        messages.error(request, 'Cannot delete admin users!')
        return redirect('admin_users')
    
    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted successfully!')
    return redirect('admin_users')

@login_required
@user_passes_test(is_admin)
def admin_donations(request):
    """Admin view to manage donations"""
    donations = Donation.objects.all().order_by('-donated_at')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        donations = donations.filter(project__title__icontains=search_query) | donations.filter(donor__username__icontains=search_query)
    
    # Pagination
    paginator = Paginator(donations, 10)  # Show 10 donations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_tab': 'donations',
        'donations': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'total_amount': Donation.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    return render(request, 'admin/donations.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_donation(request, donation_id):
    """Admin view to delete a donation"""
    donation = get_object_or_404(Donation, id=donation_id)
    
    # Update project's current amount
    project = donation.project
    project.current_amount -= donation.amount
    if project.current_amount < 0:
        project.current_amount = 0
    project.save()
    
    donation.delete()
    messages.success(request, f'Donation of ${donation.amount} deleted successfully!')
    return redirect('admin_donations')

@login_required
@user_passes_test(is_admin)
def admin_comments(request):
    """Admin view to manage comments"""
    comments = Comment.objects.all().order_by('-created_at')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        comments = comments.filter(content__icontains=search_query) | comments.filter(user__username__icontains=search_query)
    
    # Pagination
    paginator = Paginator(comments, 10)  # Show 10 comments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_tab': 'comments',
        'comments': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'admin/comments.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_comment(request, comment_id):
    """Admin view to delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    messages.success(request, 'Comment deleted successfully!')
    return redirect('admin_comments')

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """Admin view for platform settings"""
    # This is a placeholder for platform settings
    # You can implement actual settings functionality here
    
    context = {
        'active_tab': 'settings',
    }
    
    return render(request, 'admin/settings.html', context)