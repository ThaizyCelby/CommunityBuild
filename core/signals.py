# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProfessionPost, Comment, FlaggedContent
from .services.ai_matcher import AIProjectMatcher

@receiver(post_save, sender=ProfessionPost)
@receiver(post_save, sender=Comment)
def moderate_content(sender, instance, created, **kwargs):
    if created:  # Only moderate new content
        matcher = AIProjectMatcher()
        text = instance.content
        if sender == ProfessionPost:
            text = instance.title + "\n" + instance.content
        result = matcher.moderate_content(text)
        if result.get('flagged'):
            FlaggedContent.objects.create(
                content_type='post' if sender == ProfessionPost else 'comment',
                post=instance if sender == ProfessionPost else None,
                comment=instance if sender == Comment else None,
                reason=", ".join(result['reasons']),
                severity=max(result['scores'].values()) if result['scores'] else 0.5
            )