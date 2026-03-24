# core/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profession, Professional, Project, ProjectRole
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Seed the database with sample South African data'

    def handle(self, *args, **kwargs):
        # Professions
        professions_data = [
            ("Mechanic", "Repairs and maintains vehicles and machinery."),
            ("Civil Engineer", "Designs and supervises construction projects."),
            ("Architect", "Plans and designs buildings."),
            ("Construction Foreman", "Oversees on‑site workers."),
            ("Bricklayer", "Lays bricks and blocks."),
            ("Plumber", "Installs and repairs water systems."),
            ("Electrician", "Handles electrical wiring and systems."),
            ("Project Manager", "Manages project timelines and budgets."),
            ("Quantity Surveyor", "Manages costs and contracts."),
            ("Safety Officer", "Ensures compliance with health and safety regulations."),
            ("Painter", "Applies paint, finishes, and protective coatings."),  # <-- added
        ]

        for name, desc in professions_data:
            prof, created = Profession.objects.get_or_create(name=name, defaults={"description": desc})
            if created:
                self.stdout.write(f"Created profession: {name}")

        # Sample Users (regular users, not superusers)
        users = []
        names = [
            ("Thabo", "Mbeki", "thabo@example.com"),
            ("Zanele", "Dlamini", "zanele@example.com"),
            ("Sipho", "Ndlovu", "sipho@example.com"),
            ("Lerato", "Mokoena", "lerato@example.com"),
        ]
        for first, last, email in names:
            username = f"{first.lower()}_{last.lower()}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                }
            )
            if created:
                user.set_password("password123")  # set a default password (change in production)
                user.save()
                self.stdout.write(f"Created user: {username}")
                users.append(user)
            else:
                users.append(user)

        # Professionals linked to those users
        locations = ["Soweto, Johannesburg", "Khayelitsha, Cape Town", "Umlazi, Durban", "Tembisa, Ekurhuleni"]
        professions = list(Profession.objects.all())
        for i, user in enumerate(users):
            professional, created = Professional.objects.get_or_create(
                user=user,
                defaults={
                    "profession": professions[i % len(professions)],
                    "years_experience": random.randint(2, 12),
                    "location": locations[i % len(locations)],
                    "bio": f"I am a {professions[i % len(professions)].name} with experience in community projects.",
                    "is_verified": True,
                    "is_supervisor": random.choice([True, False]),
                }
            )
            if created:
                self.stdout.write(f"Created professional: {user.get_full_name()}")

        # Sample Projects
        projects_data = [
            {
                "name": "Reconstruction of RDP Houses – Soweto",
                "description": "Reconstruct 30 RDP houses damaged during storms.",
                "location": "Soweto, Johannesburg",
                "estimated_budget": 3600000.00,
                "benefits": "Decent shelter, improved safety.",
                "requirements": "NHBRC registration, CIDB grade 5.",
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=180),
                "roles": [
                    ("Civil Engineer", 1, 500000.00),
                    ("Construction Foreman", 2, 400000.00),
                    ("Bricklayer", 8, 800000.00),
                    ("Plumber", 2, 200000.00),
                    ("Electrician", 2, 200000.00),
                ]
            },
            {
                "name": "School Upgrade – Khayelitsha",
                "description": "Upgrade toilets, fix roofs, and paint classrooms.",
                "location": "Khayelitsha, Cape Town",
                "estimated_budget": 1500000.00,
                "benefits": "Better learning environment.",
                "requirements": "Approved building plans, asbestos removal cert.",
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=120),
                "roles": [
                    ("Architect", 1, 150000.00),
                    ("Plumber", 1, 120000.00),
                    ("Electrician", 1, 120000.00),
                    ("Painter", 4, 250000.00),
                ]
            },
            {
                "name": "Community Hall Construction – Umlazi",
                "description": "Build a multipurpose hall with kitchen and ablutions.",
                "location": "Umlazi, Durban",
                "estimated_budget": 2800000.00,
                "benefits": "Community events, economic opportunities.",
                "requirements": "Public building regulations, environmental impact study.",
                "start_date": date.today() + timedelta(days=30),
                "end_date": date.today() + timedelta(days=300),
                "roles": [
                    ("Civil Engineer", 1, 400000.00),
                    ("Architect", 1, 300000.00),
                    ("Construction Foreman", 1, 250000.00),
                    ("Bricklayer", 6, 500000.00),
                ]
            }
        ]

        for proj_data in projects_data:
            project, created = Project.objects.get_or_create(
                name=proj_data["name"],
                defaults={
                    "description": proj_data["description"],
                    "location": proj_data["location"],
                    "estimated_budget": proj_data["estimated_budget"],
                    "benefits": proj_data["benefits"],
                    "requirements": proj_data["requirements"],
                    "start_date": proj_data["start_date"],
                    "end_date": proj_data["end_date"],
                    "is_active": True,
                }
            )
            if created:
                for role_name, qty, budget in proj_data["roles"]:
                    # Use get_or_create in case the profession was missing from the list
                    profession, _ = Profession.objects.get_or_create(name=role_name)
                    ProjectRole.objects.create(
                        project=project,
                        profession=profession,
                        quantity_needed=qty,
                        budget_allocation=budget,
                    )
                self.stdout.write(f"Created project: {project.name}")
            else:
                self.stdout.write(f"Project already exists: {project.name}")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))