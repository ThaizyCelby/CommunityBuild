from django.db import models
from django.contrib.auth.models import User

class Profession(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Professional(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.SET_NULL, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    certificate = models.FileField(upload_to='certs/', blank=True, null=True, help_text="Upload certification")
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    is_supervisor = models.BooleanField(default=False, help_text="Check if qualified to supervise")
    last_ai_match = models.JSONField(null=True, blank=True, help_text="Cached AI matching results")

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2)
    benefits = models.TextField()
    requirements = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProjectRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE)
    quantity_needed = models.PositiveIntegerField(default=1)
    budget_allocation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ('project', 'profession')

class ProfessionPost(models.Model):
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(ProfessionPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Inquiry(models.Model):
    """Citizen inquiries for municipality"""
    citizen_name = models.CharField(max_length=100)
    citizen_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ai_drafted_response = models.TextField(blank=True, null=True)
    final_response = models.TextField(blank=True, null=True)
    is_responded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.subject} - {self.citizen_name}"

class FlaggedContent(models.Model):
    CONTENT_TYPES = [
        ('post', 'Profession Post'),
        ('comment', 'Comment'),
    ]
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    post = models.ForeignKey(ProfessionPost, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()  # AI explanation
    severity = models.FloatField()  # 0-1 confidence
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flagged {self.content_type} - {self.reason[:50]}"

class Inquiry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='inquiries')
    citizen_name = models.CharField(max_length=100)
    citizen_email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ai_drafted_response = models.TextField(blank=True, null=True)
    final_response = models.TextField(blank=True, null=True)
    is_responded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.subject} - {self.citizen_name}"

class Bid(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='bids')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bids')
    proposed_budget = models.DecimalField(max_digits=12, decimal_places=2, help_text="Proposed cost (Rands)")
    proposal_text = models.TextField(help_text="Explain how you will reduce costs while maintaining quality")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True, help_text="Municipality feedback")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Bid by {self.professional.user.username} on {self.project.name}"

class BidDocument(models.Model):
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='bids/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Document for bid {self.bid.id}"