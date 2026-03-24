import json
import re
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AIProjectMatcher:
    def __init__(self):
        self.weights = {
            'profession_match': 40,
            'experience_match': 20,
            'skills_match': 15,
            'location_match': 10,
            'verification': 10,
            'supervisor': 5,
        }

    def match_professional_to_projects(self, professional, projects, force_refresh=False):
        """Return dummy matches for up to 3 projects (South African context)"""
        matches = []
        for i, project in enumerate(projects[:3]):
            strengths = [
                f"Relevant {professional.profession.name if professional.profession else 'professional'} experience",
                "Valid Matric / NQF certificate" if professional.is_verified else "Working towards certification",
                "Good location match" if professional.location else "Willing to travel",
                "Available for immediate start"
            ]
            gaps = []
            if i == 0:
                gaps.append("Requires SACPCMP registration")
            if not professional.is_verified:
                gaps.append("Verification pending")
            if professional.years_experience < 2:
                gaps.append("Limited experience")

            matches.append({
                "project_id": project.id,
                "project_name": project.name,
                "match_score": 85 - i * 10,
                "strengths": strengths[:3],
                "gaps": gaps[:2],
                "recommendation": ["Strong Match", "Potential Match", "Potential Match"][i] if i < 3 else "Not Recommended"
            })
        if not matches:
            matches = [{
                "project_id": 0,
                "project_name": "Demo Project: Soweto School Upgrade",
                "match_score": 78,
                "strengths": ["Your profile matches this project's needs", "Location suitable"],
                "gaps": [],
                "recommendation": "Strong Match"
            }]
        # Cache results for 24h
        if hasattr(professional, 'last_ai_match'):
            professional.last_ai_match = {
                'timestamp': timezone.now().isoformat(),
                'results': matches
            }
            professional.save(update_fields=['last_ai_match'])
        return matches

    def generate_project_recommendations(self, location, community_profile=""):
        """Return 3 dummy projects based on location (South African context, Rands)"""
        return [
            {
                "project_name": f"RDP Housing Development – {location}",
                "description": "Construct 50 low-cost houses under the national housing programme.",
                "required_professions": ["Civil Engineer", "Construction Foreman", "Bricklayer", "Plumber", "Electrician"],
                "headcount": {
                    "Civil Engineer": 1,
                    "Construction Foreman": 2,
                    "Bricklayer": 10,
                    "Plumber": 3,
                    "Electrician": 3
                },
                "estimated_budget": 4500000.00,
                "timeline_months": 12,
                "benefits": ["Provides shelter for 50 families", "Local employment", "Skills transfer"],
                "requirements": "SACPCMP registration for engineer, NHBRC registration for contractor, valid CIDB grading."
            },
            {
                "project_name": f"School Infrastructure Upgrade – {location}",
                "description": "Renovate and upgrade a local primary school (roofing, sanitation, new classrooms).",
                "required_professions": ["Architect", "Structural Engineer", "Plumber", "Electrician", "Painter"],
                "headcount": {
                    "Architect": 1,
                    "Structural Engineer": 1,
                    "Plumber": 2,
                    "Electrician": 2,
                    "Painter": 4
                },
                "estimated_budget": 2800000.00,
                "timeline_months": 8,
                "benefits": ["Improved learning environment", "Job creation for locals", "Compliance with DBE norms"],
                "requirements": "SANS 10400 building standards, approved municipal plans, asbestos removal certification."
            },
            {
                "project_name": f"Community Hall & Multi-purpose Centre – {location}",
                "description": "Build a new hall for community events, meetings, and small business incubation.",
                "required_professions": ["Architect", "Civil Engineer", "Project Manager", "Carpenter", "Electrician"],
                "headcount": {
                    "Architect": 1,
                    "Civil Engineer": 1,
                    "Project Manager": 1,
                    "Carpenter": 4,
                    "Electrician": 2
                },
                "estimated_budget": 3500000.00,
                "timeline_months": 10,
                "benefits": ["Community cohesion", "Venue for local businesses", "Economic hub"],
                "requirements": "Public building regulations, accessibility standards, zoning approval."
            }
        ]

    def generate_inquiry_response(self, inquiry_message):
        return "Thank you for your enquiry. Your message has been logged and will be attended to by the relevant municipal department within 5 working days."

    def project_insights(self, project):
        roles = project.projectrole_set.all()
        if roles:
            total_jobs = sum(role.quantity_needed for role in roles)
            jobs_text = f"Creates {total_jobs} local jobs."
        else:
            jobs_text = "Potential for local job creation (roles not yet specified)."

        return f"""
### Budget Allocation
- Total budget: R{project.estimated_budget:,.2f}
- Recommended allocation: Labour (45%), Materials (35%), Contingency (10%), Overheads (5%).
- A 10% contingency is strongly advised due to fluctuating material costs.

### Potential Risks
- Delays in municipal approval (typical 2–3 months).
- Contractor availability – CIDB grading requirements may limit bidders.
- Weather interruptions during rainy season (November–March).

### Timeline Optimisation
- Phasing: Pre-construction (planning/approvals) – 3 months; Construction – 6 months; Handover – 1 month.
- Consider fast‑tracking approvals by engaging the municipality early.

### Community Benefits
- {jobs_text}
- Skills development through learnerships (SETA-aligned).
- Improved infrastructure will boost property values and economic activity.
"""

    def moderate_content(self, text):
        return {"flagged": False, "reasons": []}

    def _fallback_match(self, professional, projects):
        return self.match_professional_to_projects(professional, projects)

    # Placeholder methods to avoid errors
    def _is_cache_valid(self, professional):
        return False
    def _extract_skills_from_bio(self, bio):
        return []
    def _location_similarity(self, prof_location, project_location):
        return 0.5
    def _prepare_professional_data(self, professional):
        return {}
    def _prepare_project_data(self, project):
        return {}
    def _ai_match(self, professional, projects):
        return self.match_professional_to_projects(professional, projects)
    def _build_matching_prompt(self, professional, projects):
        return ""
    def _parse_response(self, content):
        return []