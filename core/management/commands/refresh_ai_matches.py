# core/management/commands/refresh_ai_matches.py
from django.core.management.base import BaseCommand
from core.models import Professional
from core.services.ai_matcher import AIProjectMatcher


class Command(BaseCommand):
    help = 'Refresh AI matches for all professionals'

    def handle(self, *args, **options):
        matcher = AIProjectMatcher()
        for prof in Professional.objects.filter(is_verified=True):
            projects = Project.objects.filter(is_active=True)[:10]
            matcher.match_professional_to_projects(prof, projects, force_refresh=True)
            self.stdout.write(f"Updated {prof.user.username}")