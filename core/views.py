from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Count
from django.utils import timezone
from django.core.cache import cache  # <-- added missing import
from datetime import datetime, timedelta
import json
from django.forms import inlineformset_factory
from .models import Project, ProjectRole
from .forms import ProjectForm, ProjectRoleForm
from .models import Bid, BidDocument
from .forms import BidForm, BidReviewForm
from django.core.exceptions import PermissionDenied


from .models import Profession, Professional, Project, ProjectRole, ProfessionPost, Comment, Inquiry, FlaggedContent
from .forms import UserRegisterForm, ProfessionalProfileForm, PostForm, CommentForm
from .services.ai_matcher import AIProjectMatcher
from django.contrib.admin.views.decorators import staff_member_required


def home(request):
    professionals_count = Professional.objects.count()
    projects_count = Project.objects.filter(is_active=True).count()
    professions = Profession.objects.annotate(pro_count=Count('professional')).order_by('-pro_count')[:5]
    context = {
        'professionals_count': professionals_count,
        'projects_count': projects_count,
        'top_professions': professions,
    }
    return render(request, 'core/home.html', context)


def professional_list(request):
    profession_id = request.GET.get('profession')
    professionals = Professional.objects.filter(is_verified=True).select_related('profession', 'user')
    if profession_id:
        professionals = professionals.filter(profession_id=profession_id)
    professions = Profession.objects.all()
    return render(request, 'core/professional_list.html', {
        'professionals': professionals,
        'professions': professions,
        'selected': int(profession_id) if profession_id else None
    })


def professional_detail(request, pk):
    professional = get_object_or_404(Professional.objects.select_related('user', 'profession'), pk=pk)

    def get_fresh_matches(prof):
        matcher = AIProjectMatcher()
        projects = Project.objects.filter(is_active=True)[:10]
        try:
            recommendations = matcher.match_professional_to_projects(prof, projects)
            return recommendations, None
        except Exception as e:
            return [], str(e)

    ai_error = None
    if hasattr(professional, 'last_ai_match') and professional.last_ai_match and professional.last_ai_match.get('timestamp'):
        try:
            last_time = datetime.fromisoformat(professional.last_ai_match['timestamp'])
            if timezone.now() - last_time < timedelta(hours=24):
                ai_recommendations = professional.last_ai_match['results']
            else:
                ai_recommendations, ai_error = get_fresh_matches(professional)
        except (ValueError, KeyError):
            ai_recommendations, ai_error = get_fresh_matches(professional)
    else:
        ai_recommendations, ai_error = get_fresh_matches(professional)

    recommended_projects = Project.objects.filter(
        is_active=True,
        projectrole__profession=professional.profession
    ).distinct()[:5]

    context = {
        'professional': professional,
        'recommended_projects': recommended_projects,
        'ai_recommendations': ai_recommendations,
        'ai_error': ai_error,  # pass error to template
    }
    return render(request, 'core/professional_detail.html', context)


def project_list(request):
    projects = Project.objects.filter(is_active=True).prefetch_related('projectrole_set__profession')
    return render(request, 'core/project_list.html', {'projects': projects})


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    roles = project.projectrole_set.all().select_related('profession')
    # Get qualified local professionals for each role
    qualified = {}
    for role in roles:
        profs = Professional.objects.filter(
            profession=role.profession,
            is_verified=True,
            location__icontains=project.location.split(',')[0]  # simple location match
        )
        qualified[role.profession.name] = profs
    # Prepare budget data for chart
    budget_labels = [role.profession.name for role in roles if role.budget_allocation]
    budget_data = [float(role.budget_allocation) for role in roles if role.budget_allocation]
    context = {
        'project': project,
        'roles': roles,
        'qualified': qualified,
        'budget_labels': json.dumps(budget_labels),
        'budget_data': json.dumps(budget_data),
    }
    return render(request, 'core/project_detail.html', context)


@login_required
def post_list(request, profession_id):
    profession = get_object_or_404(Profession, pk=profession_id)
    posts = profession.posts.all().order_by('-created_at')
    return render(request, 'core/post_list.html', {'profession': profession, 'posts': posts})


def post_list_all(request):
    posts = ProfessionPost.objects.all().select_related('profession', 'author').order_by('-created_at')
    return render(request, 'core/post_list_all.html', {'posts': posts})


def post_detail(request, profession_id, post_id):
    post = get_object_or_404(ProfessionPost, id=post_id, profession_id=profession_id)
    comments = post.comments.all().order_by('-created_at')
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'core/post_detail.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_list', profession_id=post.profession.id)
    else:
        form = PostForm()
    return render(request, 'core/post_form.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(ProfessionPost, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('post_detail', profession_id=post.profession.id, post_id=post.id)
    else:
        form = CommentForm()
    return redirect('post_detail', profession_id=post.profession.id, post_id=post.id)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # create empty professional profile
            Professional.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Account created! Please complete your profile.')
            return redirect('edit_profile')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})


@login_required
def edit_profile(request):
    professional, created = Professional.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfessionalProfileForm(request.POST, request.FILES, instance=professional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('professional_detail', pk=professional.pk)
    else:
        form = ProfessionalProfileForm(instance=professional)
    return render(request, 'core/profile_form.html', {'form': form})

def submit_inquiry(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name and email and subject and message:
            inquiry = Inquiry.objects.create(
                citizen_name=name,
                citizen_email=email,
                subject=subject,
                message=message,
                user=request.user if request.user.is_authenticated else None  # link user if logged in
            )
            messages.success(request, 'Your inquiry has been submitted. We will respond soon.')
            return redirect('home')
        else:
            messages.error(request, 'All fields are required.')
    return render(request, 'core/submit_inquiry.html')

@login_required
def my_inquiries(request):
    inquiries = Inquiry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_inquiries.html', {'inquiries': inquiries})

# ==================== Municipality Views ====================

@staff_member_required
def municipality_dashboard(request):
    projects = Project.objects.filter(is_active=True)
    flagged_posts = FlaggedContent.objects.filter(reviewed=False).select_related('post', 'comment')
    inquiries = Inquiry.objects.filter(is_responded=False).order_by('-created_at')
    stats = {
        'total_projects': projects.count(),
        'total_professionals': Professional.objects.filter(is_verified=True).count(),
        'pending_inquiries': inquiries.count(),
        'flagged_items': flagged_posts.count(),
    }

    # AI-generated project recommendations – cached for 24 hours
    recommendations = cache.get('municipality_recommendations')
    if not recommendations:
        # Default location: use first project's location or a placeholder
        default_location = "Community"
        if projects.exists():
            default_location = projects.first().location
        # Gather community profile from recent inquiries
        recent_inquiries = Inquiry.objects.filter(is_responded=False).order_by('-created_at')[:5]
        profile_text = " ".join([inq.message for inq in recent_inquiries]) if recent_inquiries else "General community development"
        matcher = AIProjectMatcher()
        recommendations = matcher.generate_project_recommendations(default_location, profile_text)
        # Cache for 24 hours (86400 seconds)
        cache.set('municipality_recommendations', recommendations, 86400)

    context = {
        'projects': projects,
        'flagged_posts': flagged_posts,
        'inquiries': inquiries,
        'stats': stats,
        'recommendations': recommendations[:3] if recommendations else [],  # show top 3
    }
    return render(request, 'core/municipality/dashboard.html', context)


@staff_member_required
def project_insights(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    matcher = AIProjectMatcher()
    insights = matcher.project_insights(project)
    return render(request, 'core/municipality/project_insights.html', {'project': project, 'insights': insights})


@staff_member_required
def inquiry_list(request):
    inquiries = Inquiry.objects.all().order_by('-created_at')
    return render(request, 'core/municipality/inquiry_list.html', {'inquiries': inquiries})


@staff_member_required
def inquiry_detail(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    if request.method == 'POST':
        final_response = request.POST.get('final_response')
        inquiry.final_response = final_response
        inquiry.is_responded = True
        inquiry.responded_at = timezone.now()
        inquiry.save()
        messages.success(request, 'Response sent.')
        return redirect('inquiry_list')
    # If AI draft not yet generated, generate one
    if not inquiry.ai_drafted_response:
        matcher = AIProjectMatcher()
        inquiry.ai_drafted_response = matcher.generate_inquiry_response(inquiry.message)
        inquiry.save()
    return render(request, 'core/municipality/inquiry_detail.html', {'inquiry': inquiry})


@staff_member_required
def flagged_content_list(request):
    flagged = FlaggedContent.objects.filter(reviewed=False).select_related('post', 'comment')
    return render(request, 'core/municipality/flagged_list.html', {'flagged': flagged})


@staff_member_required
def flagged_content_review(request, flagged_id):
    flagged = get_object_or_404(FlaggedContent, id=flagged_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            flagged.reviewed = True
            flagged.save()
            messages.success(request, 'Content approved.')
        elif action == 'delete':
            if flagged.content_type == 'post' and flagged.post:
                flagged.post.delete()
            elif flagged.content_type == 'comment' and flagged.comment:
                flagged.comment.delete()
            flagged.delete()
            messages.success(request, 'Content deleted.')
        return redirect('flagged_content_list')
    return render(request, 'core/municipality/flagged_review.html', {'flagged': flagged})


def project_recommendations(request):
    """Manual form for generating custom AI recommendations (if user wants to override)"""
    if request.method == 'POST':
        location = request.POST.get('location')
        community_profile = request.POST.get('community_profile', '')
        matcher = AIProjectMatcher()
        recommendations = matcher.generate_project_recommendations(location, community_profile)
        return render(request, 'core/municipality/project_recommendations.html', {
            'recommendations': recommendations,
            'location': location,
            'profile': community_profile
        })
    return render(request, 'core/municipality/request_recommendations.html')


# ==================== Professional Recommendations Page ====================

@login_required
def professional_recommendations(request):
    professional = get_object_or_404(Professional, user=request.user)
    matcher = AIProjectMatcher()
    projects = Project.objects.filter(is_active=True)[:20]
    recommendations = matcher.match_professional_to_projects(professional, projects, force_refresh=False)
    context = {
        'professional': professional,
        'recommendations': recommendations,
    }
    return render(request, 'core/professional_recommendations.html', context)

@staff_member_required
def project_create(request):
    ProjectRoleFormSet = inlineformset_factory(
        Project, ProjectRole,
        form=ProjectRoleForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        formset = ProjectRoleFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            project = form.save()
            formset.instance = project
            formset.save()
            messages.success(request, 'Project created successfully.')
            return redirect('municipality_dashboard')
    else:
        form = ProjectForm()
        formset = ProjectRoleFormSet()

    return render(request, 'core/municipality/project_form.html', {
        'form': form,
        'formset': formset,
    })

from .models import Bid, BidDocument
from .forms import BidForm, BidReviewForm
from django.core.exceptions import PermissionDenied

@login_required
def bid_create(request, project_id):
    project = get_object_or_404(Project, id=project_id, is_active=True)
    professional = get_object_or_404(Professional, user=request.user)
    # Optional: check if already bid? We'll allow multiple bids, but you may limit.
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.professional = professional
            bid.project = project
            bid.save()
            # Handle multiple document uploads (if any)
            files = request.FILES.getlist('documents')
            for f in files:
                BidDocument.objects.create(bid=bid, file=f)
            messages.success(request, 'Your bid has been submitted successfully.')
            return redirect('professional_detail', pk=professional.pk)
    else:
        form = BidForm()
    return render(request, 'core/bid_form.html', {'form': form, 'project': project})

@login_required
def my_bids(request):
    professional = get_object_or_404(Professional, user=request.user)
    bids = Bid.objects.filter(professional=professional).order_by('-submitted_at')
    return render(request, 'core/my_bids.html', {'bids': bids})

@login_required
def bid_detail(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    # Professionals can see their own bids; staff can see any
    if request.user != bid.professional.user and not request.user.is_staff:
        raise PermissionDenied
    return render(request, 'core/bid_detail.html', {'bid': bid})

@staff_member_required
def municipality_bids(request):
    bids = Bid.objects.select_related('professional__user', 'project').order_by('-submitted_at')
    return render(request, 'core/municipality/bid_list.html', {'bids': bids})

@staff_member_required
def review_bid(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id)
    if request.method == 'POST':
        form = BidReviewForm(request.POST, instance=bid)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.reviewed_at = timezone.now()
            bid.save()
            messages.success(request, f'Bid {bid.get_status_display()}.')
            return redirect('municipality_bids')
    else:
        form = BidReviewForm(instance=bid)
    return render(request, 'core/municipality/review_bid.html', {'form': form, 'bid': bid})
