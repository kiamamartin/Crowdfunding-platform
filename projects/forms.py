from django import forms
from .models import Project, Donation, Comment

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'goal_amount', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class DonationForm(forms.Form):
    amount = forms.DecimalField(min_value=1, decimal_places=2)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']