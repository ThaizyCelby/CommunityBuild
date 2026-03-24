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
            model="models/gemini-2.0-flash",   # <-- updated model name
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1500
            )
        )
        content = response.text
        print("="*50)
        print("RAW GEMINI RESPONSE:")
        print(content)
        print("="*50)
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print("No JSON array found in response")
            return []
    except Exception as e:
        logger.error(f"Project recommendation error: {e}")
        # Fallback: return some generic project ideas
        return [
            {
                "project_name": f"Community Garden in {location}",
                "description": "Create a shared green space for residents to grow food and connect.",
                "required_professions": ["Landscape Architect", "Gardener", "Project Manager"],
                "headcount": {"Landscape Architect": 1, "Gardener": 3, "Project Manager": 1},
                "estimated_budget": 50000.0,
                "timeline_months": 6,
                "benefits": ["Improved food security", "Community bonding", "Green space"],
                "requirements": "Land, water access, volunteers."
            },
            {
                "project_name": f"Sidewalk Repair in {location}",
                "description": "Fix broken sidewalks to improve pedestrian safety.",
                "required_professions": ["Civil Engineer", "Construction Worker"],
                "headcount": {"Civil Engineer": 1, "Construction Worker": 4},
                "estimated_budget": 120000.0,
                "timeline_months": 4,
                "benefits": ["Safer walking", "Accessibility"],
                "requirements": "Permits, materials."
            }
        ]