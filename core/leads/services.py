from django.db.models import Avg, Count
from communication.models import Email, Call, Meeting

class LeadScoringService:
    """
    Service class for lead scoring operations and intelligence.
    """
    
    @staticmethod
    def calculate_lead_score(lead):
        """
        Recalculate the entire lead score based on profile and interactions.
        """
        score = 0
        
        # 1. Profile Completeness (Max 40 points)
        if lead.email: score += 10
        if lead.phone: score += 10
        if lead.job_title: score += 5
        if lead.company: score += 5
        if lead.industry: score += 5
        if lead.description: score += 5
        
        # 2. Interaction Activity (Max 40 points)
        email_count = Email.objects.filter(lead=lead).count()
        call_count = Call.objects.filter(lead=lead).count()
        meeting_count = Meeting.objects.filter(lead=lead).count()
        
        score += min(20, email_count * 2)
        score += min(10, call_count * 5)
        score += min(10, meeting_count * 10)
        
        # 3. Sentiment Analysis (Max 20 points)
        # Calculate average sentiment across all interactions
        interactions = list(Email.objects.filter(lead=lead)) + \
                       list(Call.objects.filter(lead=lead)) + \
                       list(Meeting.objects.filter(lead=lead))
        
        if interactions:
            avg_sentiment = sum(i.sentiment_score for i in interactions) / len(interactions)
            # Map -1.0 to 1.0 range to -10 to +20 points
            if avg_sentiment > 0.5: score += 20
            elif avg_sentiment > 0: score += 10
            elif avg_sentiment < -0.5: score -= 10
            
        # Cap at 100
        lead.lead_score = max(0, min(100, score))
        lead.save(update_fields=['lead_score'])
        
        # Trigger status update
        lead.update_status_from_score()
        
        return lead.lead_score

    @staticmethod
    def get_next_best_action(lead):
        """
        Determine the Next Best Action (NBA) for a lead.
        """
        # 1. Status-based actions
        if lead.status == 'new':
            return {
                "action": "Qualify Lead",
                "description": "Review profile and initial data to determine fit.",
                "icon": "bi-check-circle",
                "priority": "high"
            }
            
        if lead.status == 'qualified' and lead.lead_score > 70:
            return {
                "action": "Convert to Opportunity",
                "description": "Lead score is high. Convert to deal now.",
                "icon": "bi-currency-dollar",
                "priority": "critical"
            }

        # 2. Time-based actions
        last_email = Email.objects.filter(lead=lead).order_by('-timestamp').first()
        last_call = Call.objects.filter(lead=lead).order_by('-timestamp').first()
        
        last_interaction = None
        if last_email and last_call:
            last_interaction = max(last_email.timestamp, last_call.timestamp)
        elif last_email:
            last_interaction = last_email.timestamp
        elif last_call:
            last_interaction = last_call.timestamp
            
        if last_interaction:
            days_since = (timezone.now() - last_interaction).days
            if days_since > 14:
                return {
                    "action": "Re-engage Lead",
                    "description": f"No interaction in {days_since} days. Send a check-in email.",
                    "icon": "bi-envelope",
                    "priority": "medium"
                }
            elif days_since > 7:
                 return {
                    "action": "Follow Up",
                    "description": "It's been a week. Give them a call.",
                    "icon": "bi-telephone",
                    "priority": "medium"
                }

        # 3. Default
        return {
            "action": "Log Interaction",
            "description": "Record a call, email, or meeting to build history.",
            "icon": "bi-pencil-square",
            "priority": "low"
        }

    @staticmethod
    def update_lead_score(lead_id, score_increment, reason=""):
        """
        Legacy wrapper for manual updates, triggers full recalculation.
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            # For manual updates, we might just add points directly or trigger full recalc
            # Here we'll just trigger full recalc to keep it consistent
            return LeadScoringService.calculate_lead_score(lead)
        except Lead.DoesNotExist:
            return None
    
    @staticmethod
    def get_scoring_recommendations(lead):
        """
        Get recommendations for improving lead score.
        """
        recommendations = []
        
        if not lead.email: recommendations.append("Add email address (+10 points)")
        if not lead.phone: recommendations.append("Add phone number (+10 points)")
        if not lead.job_title: recommendations.append("Add job title (+5 points)")
        if not lead.description: recommendations.append("Add lead description (+5 points)")
        
        # Interaction recommendations
        email_count = Email.objects.filter(lead=lead).count()
        if email_count == 0:
            recommendations.append("Send first email (+2 points)")
            
        return recommendations