from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Professional, ProfessionPost, Comment, Project, ProjectRole  # added Project, ProjectRole
from .models import Bid

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class ProfessionalProfileForm(forms.ModelForm):
    class Meta:
        model = Professional
        fields = ['profession', 'profile_pic', 'certificate', 'bio', 'location', 'years_experience', 'is_supervisor']

class PostForm(forms.ModelForm):
    class Meta:
        model = ProfessionPost
        fields = ['profession', 'title', 'content']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

# New forms for project creation
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'location', 'estimated_budget',
                  'benefits', 'requirements', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProjectRoleForm(forms.ModelForm):
    class Meta:
        model = ProjectRole
        fields = ['profession', 'quantity_needed', 'budget_allocation']

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['proposed_budget', 'proposal_text']
        widgets = {
            'proposal_text': forms.Textarea(attrs={'rows': 4}),
        }

class BidReviewForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['status', 'feedback']