"""
Multi-modal Intelligence - Voice & Text Analysis.
Handles call transcriptions and combined sentiment analysis.
"""

from typing import Dict, Any, List, Optional
import logging
from ml_models.services.intelligence.nlp_service import NLPService

class VoiceIntelligenceService:
    """
    Service for analyzing multi-modal data (Voice/Audio transcripts + Text).
    """
    
    def __init__(self):
        self.logger = logging.getLogger("intelligence.voice")
        self.nlp = NLPService()
        
    def analyze_call_transcript(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyzes a call transcript for sentiment, entities, and intent.
        """
        self.logger.info("Analyzing call transcript...")
        
        # 1. Basic NLP analysis
        sentiment = self.nlp.analyze_sentiment(transcript)
        entities = self.nlp.extract_entities(transcript)
        
        # 2. Extract call-specific patterns (high-level)
        # e.g., "price mentioned", "competitor mentioned"
        lower_transcript = transcript.lower()
        price_mentioned = any(word in lower_transcript for word in ["price", "cost", "budget", "expensive"])
        competitor_detected = any(word in lower_transcript for word in ["competitor", "alternative"])
        
        return {
            "transcript_summary": transcript[:100] + "...",
            "sentiment": sentiment,
            "entities": entities,
            "insights": {
                "price_discussed": price_mentioned,
                "competitor_alert": competitor_detected,
                "overall_tone": "positive" if sentiment.get('score', 0) > 0.5 else "negative"
            }
        }

    def combine_engagement_signals(self, email_engagement: float, call_engagement: float) -> float:
        """
        Combines signals from different communication modes into a unified health score.
        """
        # Weighted average of engagement signals
        return (email_engagement * 0.4) + (call_engagement * 0.6)
