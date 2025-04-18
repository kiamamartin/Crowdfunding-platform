from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import Project, Donation
from .forms import ProjectForm, DonationForm, CommentForm
from django.contrib.auth import logout 



def home(request):
    featured_projects = Project.objects.all().order_by('-current_amount')[:6]
    
    # Calculate progress percentage and days left for each project
    for project in featured_projects:
        project.progress = int((project.current_amount / project.goal_amount) * 100)
        project.days_left = (project.deadline - timezone.now().date()).days
    
    return render(request, 'projects/home.html', {
        'featured_projects': featured_projects,
    })                                                     
def project_list(request):
    projects = Project.objects.all()
    
    # Apply filters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'newest')
    
    if search_query:
        projects = projects.filter(title__icontains=search_query)
    
    if sort_by == 'newest':
        projects = projects.order_by('-created_at')
    elif sort_by == 'ending_soon':
        projects = projects.order_by('deadline')
    elif sort_by == 'most_funded':
        projects = projects.order_by('-current_amount')
    
    # Calculate progress percentage and days left for each project
    for project in projects:
        project.progress = int((project.current_amount / project.goal_amount) * 100)
        project.days_left = (project.deadline - timezone.now().date()).days
    
    return render(request, 'projects/project_list.html', {
        'projects': projects,
    })

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Calculate progress percentage and days left
    project.progress = int((project.current_amount / project.goal_amount) * 100)
    project.days_left = (project.deadline - timezone.now().date()).days
    project.backers_count = Donation.objects.filter(project=project).count()
    
    return render(request, 'projects/project_detail.html', {
        'project': project,
    })

@login_required
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/create_project.html', {
        'form': form,
    })

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/create_project.html', {
        'form': form,
        'project': project,
    })

@login_required
def donate(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            donation = Donation(
                project=project,
                donor=request.user,
                amount=amount
            )
            donation.save()
            
            # Update project's current amount
            project.current_amount += amount
            project.save()
            
            messages.success(request, f'Thank you for your donation of ${amount}!')
            return redirect('project_detail', project_id=project.id)
    
    return redirect('project_detail', project_id=project.id)

@login_required
def add_comment(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.project = project
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
    
    return redirect('project_detail', project_id=project.id)

@login_required
def dashboard(request):
    user_projects = Project.objects.filter(creator=request.user)
    user_donations = Donation.objects.filter(donor=request.user).order_by('-donated_at')
    
    # Calculate stats
    user_projects_count = user_projects.count()
    total_donations_made = Donation.objects.filter(donor=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_funding_received = Donation.objects.filter(project__creator=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate progress percentage and days left for each project
    for project in user_projects:
        project.progress = int((project.current_amount / project.goal_amount) * 100)
        project.days_left = (project.deadline - timezone.now().date()).days
    
    return render(request, 'projects/dashboard.html', {
        'user_projects': user_projects,
        'user_donations': user_donations,
        'user_projects_count': user_projects_count,
        'total_donations_made': total_donations_made,
        'total_funding_received': total_funding_received,
    })

@login_required
def project_donations(request, project_id):
    project = get_object_or_404(Project, id=project_id, creator=request.user)
    donations = Donation.objects.filter(project=project).order_by('-donated_at')
    
    return render(request, 'projects/project_donations.html', {
        'project': project,
        'donations': donations,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {
        'form': form,
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in successfully!')
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {
        'form': form,
    })
    
def user_logout(request):
        logout(request)
        messages.success(request, 'You have been logged out successfully!')
        return redirect('home')