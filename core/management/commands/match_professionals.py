from django.core.management.base import BaseCommand
from core.models import Professional, Project
from core.services.ai_matcher import AIProjectMatcher
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Run AI matching for all professionals and cache results'

    def add_arguments(self, parser):
        parser.add_argument('--professional-id', type=int, help='Match specific professional')
        parser.add_argument('--project-id', type=int, help='Match specific project')

    def handle(self, *args, **options):
        matcher = AIProjectMatcher()

        if options['professional_id']:
            # Match single professional
            professional = Professional.objects.get(id=options['professional_id'])
            projects = Project.objects.filter(is_active=True)[:10]
            results = matcher.match_professional_to_projects(professional, projects)

            # Save results (you might want to create a model to cache these)
            self.stdout.write(self.style.SUCCESS(
                f"Matched {professional.user.get_full_name()} against {len(projects)} projects"
            ))
            self.stdout.write(json.dumps(results, indent=2))

        elif options['project_id']:
            # Match single project (implement similarly)
            pass

        else:
            # Match all professionals (be careful with API costs!)
            self.stdout.write(self.style.WARNING(
                "This will use API calls for each professional. Consider limiting."
            ))