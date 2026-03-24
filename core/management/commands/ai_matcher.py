import json
import re
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AIProjectMatcher:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.weights = {
            'profession_match': 40,
            'experience_match': 20,
            'skills_match': 15,
            'location_match': 10,
            'verification': 10,
            'supervisor': 5,
        }
        logger.info(f"Gemini API Key set: {'Yes' if settings.GEMINI_API_KEY else 'No'}")

    def match_professional_to_projects(self, professional, projects, force_refresh=False):
        if not force_refresh and self._is_cache_valid(professional):
            return professional.last_ai_match['results']
        projects = projects[:10]
        try:
            matches = self._ai_match(professional, projects)
            logger.info(f"AI match successful for {professional.user.username}")
            if hasattr(professional, 'last_ai_match'):
                professional.last_ai_match = {
                    'timestamp': timezone.now().isoformat(),
                    'results': matches
                }
                professional.save(update_fields=['last_ai_match'])
            return matches
        except Exception as e:
            logger.error(f"AI match failed: {e}")
            matches = self._fallback_match(professional, projects)
            logger.info("Fallback used")
            return matches

    def _is_cache_valid(self, professional):
        if not hasattr(professional, 'last_ai_match') or not professional.last_ai_match:
            return False
        cache = professional.last_ai_match
        if not cache.get('timestamp'):
            return False
        try:
            last_time = datetime.fromisoformat(cache['timestamp'])
            return (timezone.now() - last_time).total_seconds() < 24 * 3600
        except:
            return False

    def _extract_skills_from_bio(self, bio):
        if not bio:
            return []
        skill_keywords = [
            "python", "javascript", "java", "c++", "react", "django", "flask",
            "aws", "azure", "docker", "kubernetes", "sql", "mongodb", "postgresql",
            "project management", "leadership", "communication", "teamwork",
            "civil engineering", "structural analysis", "autocad", "revit", "sketchup",
            "budgeting", "planning", "scheduling", "quality control", "safety",
            "bridge design", "road construction", "surveying", "geotechnical",
            "environmental impact", "sustainability", "construction management"
        ]
        bio_lower = bio.lower()
        found = []
        for keyword in skill_keywords:
            if keyword in bio_lower:
                found.append(keyword)
        return list(set(found))

    def _location_similarity(self, prof_location, project_location):
        if not prof_location or not project_location:
            return 0
        prof_loc_lower = prof_location.lower()
        proj_loc_lower = project_location.lower()
        if prof_loc_lower in proj_loc_lower or proj_loc_lower in prof_loc_lower:
            return 1.0
        prof_words = set(prof_loc_lower.split(',')) | set(prof_loc_lower.split())
        proj_words = set(proj_loc_lower.split(',')) | set(proj_loc_lower.split())
        if not prof_words or not proj_words:
            return 0
        overlap = len(prof_words & proj_words)
        return overlap / max(len(prof_words), len(proj_words))

    def _prepare_professional_data(self, professional):
        skills = self._extract_skills_from_bio(professional.bio)
        if professional.profession and professional.profession.name not in skills:
            skills.append(professional.profession.name)
        return {
            "name": professional.user.get_full_name(),
            "profession": professional.profession.name if professional.profession else "Unspecified",
            "years_experience": professional.years_experience,
            "location": professional.location,
            "bio": professional.bio,
            "skills": skills,
            "is_verified": professional.is_verified,
            "is_supervisor": professional.is_supervisor,
        }

    def _prepare_project_data(self, project):
        roles = project.projectrole_set.all()
        required_professions = [role.profession.name for role in roles]
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "location": project.location,
            "required_professions": required_professions,
            "estimated_budget": str(project.estimated_budget),
            "benefits": project.benefits,
            "requirements": project.requirements,
        }

    def _ai_match(self, professional, projects):
        prof_data = self._prepare_professional_data(professional)
        projects_data = [self._prepare_project_data(p) for p in projects]
        prompt = self._build_matching_prompt(prof_data, projects_data)
        logger.info("Sending request to Gemini API...")
        response = self.client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1500
            )
        )
        content = response.text
        logger.info(f"Gemini response received, length: {len(content)}")
        return self._parse_response(content)

    def _build_matching_prompt(self, professional, projects):
        prompt = f"""
You are an expert talent matching assistant. Evaluate how well this professional matches each project.

PROFESSIONAL PROFILE:
- Name: {professional['name']}
- Primary Profession: {professional['profession']}
- Years of Experience: {professional['years_experience']}
- Location: {professional['location']}
- Verified: {'Yes' if professional['is_verified'] else 'No'}
- Can Supervise: {'Yes' if professional['is_supervisor'] else 'No'}
- Skills: {', '.join(professional['skills'])}
- Bio: {professional['bio']}

PROJECTS:
{json.dumps(projects, indent=2)}

For each project, provide a JSON array with objects containing:
- project_id: integer
- match_score: integer 0-100
- strengths: list of strings
- gaps: list of strings
- recommendation: "Strong Match", "Potential Match", or "Not Recommended"

Return ONLY valid JSON, no additional text.
"""
        return prompt

    def _parse_response(self, content):
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return []
        else:
            logger.error("No JSON array found in response")
            return []

    def generate_project_recommendations(self, location, community_profile=""):
        prompt = f"""
You are an expert urban planner AI. Based on the location "{location}" and community profile: "{community_profile}", suggest 3-5 community development projects.

For each project, provide a JSON array with objects containing:
- project_name: str
- description: str
- required_professions: list of strings
- headcount: dict (profession -> number needed)
- estimated_budget: float (in USD)
- timeline_months: int
- benefits: list of strings
- requirements: str

Return ONLY valid JSON, no other text.
"""
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1500
                )
            )
            content = response.text
            json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            logger.error(f"Project recommendation error: {e}")
            return []

    def generate_inquiry_response(self, inquiry_message):
        prompt = f"""
You are an AI assistant helping a municipal official respond to a citizen's inquiry.
Draft a helpful, professional, and empathetic response.

Citizen's message:
{inquiry_message}

Draft response:
"""
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=300
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Inquiry response error: {e}")
            return "Unable to generate response at this time."

    def project_insights(self, project):
        roles = project.projectrole_set.all()
        required = [f"{role.quantity_needed} {role.profession.name}" for role in roles]
        prompt = f"""
You are a project management expert. Analyze this community project and provide insights.

Project: {project.name}
Description: {project.description}
Location: {project.location}
Budget: ${project.estimated_budget}
Required roles: {', '.join(required)}
Timeline: {project.start_date} to {project.end_date}

Provide insights on:
- Budget allocation suggestions
- Potential risks
- Timeline optimization
- Community benefits
"""
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=500
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Project insights error: {e}")
            return f"Could not generate insights: {e}"

    def moderate_content(self, text):
        prompt = f"""
Analyze this text for inappropriate content (hate speech, harassment, explicit material, spam).
If flagged, explain why. If safe, respond with "SAFE".

Text: "{text}"

Respond in JSON format: {{"flagged": true/false, "reasons": []}}
"""
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=200
                )
            )
            content = response.text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"flagged": False, "reasons": []}
        except Exception as e:
            logger.error(f"Moderation error: {e}")
            return {"flagged": False, "error": str(e)}

    def _fallback_match(self, professional, projects):
        matches = []
        for project in projects:
            score = 0
            reasons = []
            gaps = []
            project_professions = [role.profession.name for role in project.projectrole_set.all()]
            if professional.profession and professional.profession.name in project_professions:
                score += self.weights['profession_match']
                reasons.append(f"Matches required profession: {professional.profession.name}")
            else:
                gaps.append("Profession not required")
            exp = professional.years_experience
            if exp >= 5:
                score += self.weights['experience_match']
                reasons.append(f"{exp} years experience")
            elif exp >= 2:
                score += self.weights['experience_match'] * 0.5
                reasons.append(f"{exp} years experience (some)")
            else:
                gaps.append("Limited experience")
            skills = self._extract_skills_from_bio(professional.bio)
            if professional.profession and professional.profession.name not in skills:
                skills.append(professional.profession.name)
            project_text = (project.description + ' ' + project.requirements).lower()
            skill_matches = sum(1 for skill in skills if skill.lower() in project_text)
            if skill_matches > 0:
                skill_score = min(1.0, skill_matches / 3) * self.weights['skills_match']
                score += skill_score
                reasons.append(f"Skills match: {skill_matches} relevant skills")
            else:
                gaps.append("No obvious skill overlap")
            loc_sim = self._location_similarity(professional.location, project.location)
            score += loc_sim * self.weights['location_match']
            if loc_sim > 0.5:
                reasons.append("Location proximity")
            else:
                gaps.append("Location mismatch")
            if professional.is_verified:
                score += self.weights['verification']
                reasons.append("Verified professional")
            if professional.is_supervisor:
                score += self.weights['supervisor']
                reasons.append("Can supervise")
            max_possible = sum(self.weights.values())
            normalized_score = int((score / max_possible) * 100)
            if normalized_score >= 70:
                rec = "Strong Match"
            elif normalized_score >= 40:
                rec = "Potential Match"
            else:
                rec = "Not Recommended"
            matches.append({
                "project_id": project.id,
                "project_name": project.name,
                "match_score": normalized_score,
                "strengths": reasons[:3],
                "gaps": gaps[:3],
                "recommendation": rec,
            })
        return matches