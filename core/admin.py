from django.contrib import admin
from .models import Profession, Professional, Project, ProjectRole, ProfessionPost, Comment

@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('user', 'profession', 'is_verified', 'years_experience', 'location')
    list_filter = ('profession', 'is_verified', 'is_supervisor')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'estimated_budget', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'location')

class ProjectRoleInline(admin.TabularInline):
    model = ProjectRole
    extra = 1

@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    list_display = ('project', 'profession', 'quantity_needed', 'budget_allocation')
    list_filter = ('project', 'profession')

@admin.register(ProfessionPost)
class ProfessionPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'profession', 'author', 'created_at')
    list_filter = ('profession', 'created_at')
    search_fields = ('title', 'content')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    list_filter = ('created_at',)