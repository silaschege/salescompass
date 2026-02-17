"""
NLP Service - Ontology-Based Natural Language Processing

This module provides NLP services for sentiment analysis,
entity extraction, and text classification.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import logging

from ml_models.core.ontology.base import Concept, ConceptType
from ml_models.core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)


class SentimentType(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    sentiment: SentimentType
    score: float  # -1.0 to 1.0
    confidence: float
    aspects: Dict[str, SentimentType] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentiment": self.sentiment.value,
            "score": self.score,
            "confidence": self.confidence,
            "aspects": {k: v.value for k, v in self.aspects.items()}
        }


@dataclass
class ExtractedEntity:
    """An entity extracted from text"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    concept_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "concept_id": self.concept_id
        }


@dataclass
class ClassificationResult:
    """Result of text classification"""
    category: str
    confidence: float
    all_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "all_scores": self.all_scores
        }


class NLPService(ABC):
    """Abstract base class for NLP services"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or get_knowledge_graph()


class SentimentAnalyzer(NLPService):
    """
    Analyzes sentiment in text using rule-based approach
    with ontology-enhanced patterns.
    """
    
    # Sentiment lexicons (simplified)
    POSITIVE_WORDS = {
        "great", "excellent", "amazing", "fantastic", "wonderful", "love",
        "happy", "satisfied", "helpful", "easy", "impressed", "best",
        "recommend", "perfect", "outstanding", "delighted", "appreciate"
    }
    
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "hate", "disappointed",
        "frustrated", "angry", "problem", "issue", "difficult", "worst",
        "never", "broken", "useless", "waste", "poor", "complaint"
    }
    
    INTENSIFIERS = {
        "very", "extremely", "really", "incredibly", "absolutely",
        "totally", "completely", "highly"
    }
    
    NEGATORS = {"not", "no", "never", "none", "nothing", "neither", "nobody"}
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SentimentResult with sentiment type, score, and confidence
        """
        if not text:
            return SentimentResult(
                sentiment=SentimentType.NEUTRAL,
                score=0.0,
                confidence=0.0
            )
            
        words = text.lower().split()
        
        positive_count = 0
        negative_count = 0
        intensifier_active = False
        negation_active = False
        
        for i, word in enumerate(words):
            # Clean word
            word = re.sub(r'[^\w]', '', word)
            
            # Check for intensifiers
            if word in self.INTENSIFIERS:
                intensifier_active = True
                continue
                
            # Check for negators
            if word in self.NEGATORS:
                negation_active = True
                continue
                
            # Score multiplier
            multiplier = 1.5 if intensifier_active else 1.0
            if negation_active:
                multiplier *= -1
                
            # Count sentiment words
            if word in self.POSITIVE_WORDS:
                positive_count += multiplier
            elif word in self.NEGATIVE_WORDS:
                negative_count += multiplier
                
            # Reset modifiers after a few words
            if i > 0 and i % 3 == 0:
                intensifier_active = False
                negation_active = False
                
        # Calculate score
        total = positive_count + abs(negative_count)
        if total == 0:
            score = 0.0
            sentiment = SentimentType.NEUTRAL
            confidence = 0.3
        else:
            score = (positive_count - abs(negative_count)) / max(len(words) / 5, 1)
            score = max(-1.0, min(1.0, score))
            
            if score > 0.1:
                sentiment = SentimentType.POSITIVE
            elif score < -0.1:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
                
            confidence = min(0.5 + (total / len(words)) * 2, 0.95)
            
        return SentimentResult(
            sentiment=sentiment,
            score=score,
            confidence=confidence
        )
    
    def analyze_with_aspects(
        self,
        text: str,
        aspects: List[str]
    ) -> SentimentResult:
        """
        Analyze sentiment for specific aspects mentioned in text.
        
        Args:
            text: Input text
            aspects: List of aspects to check (e.g., ["price", "support", "features"])
        """
        base_result = self.analyze(text)
        aspect_sentiments = {}
        
        sentences = text.split('.')
        
        for aspect in aspects:
            aspect_lower = aspect.lower()
            for sentence in sentences:
                if aspect_lower in sentence.lower():
                    sentence_result = self.analyze(sentence)
                    aspect_sentiments[aspect] = sentence_result.sentiment
                    break
                    
        base_result.aspects = aspect_sentiments
        return base_result


class EntityExtractor(NLPService):
    """
    Extracts named entities from text and maps them to ontology concepts.
    """
    
    # Entity patterns (simplified regex-based)
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "money": r'\$[\d,]+(?:\.\d{2})?',
        "percentage": r'\d+(?:\.\d+)?%',
        "date": r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        "company_indicator": r'\b(?:Inc|Corp|LLC|Ltd|Company|Co)\b',
    }
    
    # Keywords that indicate entity types
    TYPE_KEYWORDS = {
        "person": ["mr", "mrs", "ms", "dr", "manager", "director", "ceo", "cto"],
        "company": ["company", "corp", "inc", "ltd", "llc", "organization"],
        "product": ["product", "solution", "platform", "software", "tool"],
        "issue": ["problem", "issue", "bug", "error", "complaint"],
    }
    
    def extract(self, text: str) -> List[ExtractedEntity]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Pattern-based extraction
        for entity_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    text=match.group(),
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9
                ))
                
        # Keyword-based extraction
        words = text.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip('.,!?')
            for entity_type, keywords in self.TYPE_KEYWORDS.items():
                if word_lower in keywords:
                    # Try to capture context
                    start_idx = max(0, i - 2)
                    end_idx = min(len(words), i + 2)
                    phrase = ' '.join(words[start_idx:end_idx])
                    
                    # Calculate position
                    start = text.lower().find(phrase.lower())
                    if start >= 0:
                        entities.append(ExtractedEntity(
                            text=phrase,
                            entity_type=entity_type,
                            start=start,
                            end=start + len(phrase),
                            confidence=0.6
                        ))
                        
        # Link to ontology concepts
        for entity in entities:
            entity.concept_id = self._link_to_concept(entity)
            
        return entities
    
    def _link_to_concept(self, entity: ExtractedEntity) -> Optional[str]:
        """Try to link extracted entity to an ontology concept"""
        type_mapping = {
            "issue": "case",
            "company": "account",
            "person": "contact",
            "product": "product"
        }
        
        return type_mapping.get(entity.entity_type)


class TextClassifier(NLPService):
    """
    Classifies text into predefined categories using
    keyword matching and ontology awareness.
    """
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        "sales_inquiry": [
            "pricing", "cost", "quote", "buy", "purchase", "demo",
            "trial", "subscription", "license", "discount"
        ],
        "support_request": [
            "help", "support", "issue", "problem", "error", "bug",
            "not working", "broken", "fix", "assistance"
        ],
        "feedback": [
            "feedback", "suggestion", "improve", "feature request",
            "would like", "wish", "recommend", "opinion"
        ],
        "complaint": [
            "complaint", "disappointed", "unhappy", "frustrated",
            "terrible", "worst", "refund", "cancel"
        ],
        "general_inquiry": [
            "question", "wondering", "curious", "information",
            "learn more", "details", "how does"
        ]
    }
    
    def classify(self, text: str) -> ClassificationResult:
        """
        Classify text into a category.
        
        Args:
            text: Input text to classify
            
        Returns:
            ClassificationResult with category and confidence
        """
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[category] = score / len(keywords)
            
        if not scores or max(scores.values()) == 0:
            return ClassificationResult(
                category="general_inquiry",
                confidence=0.3,
                all_scores=scores
            )
            
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        # Normalize confidence
        confidence = min(0.5 + best_score * 2, 0.95)
        
        return ClassificationResult(
            category=best_category,
            confidence=confidence,
            all_scores=scores
        )
    
    def classify_intent(self, text: str) -> ClassificationResult:
        """
        Classify the intent of a message.
        Uses category classification as base.
        """
        result = self.classify(text)
        
        # Map categories to intents
        intent_mapping = {
            "sales_inquiry": "purchase_intent",
            "support_request": "support_intent",
            "feedback": "feedback_intent",
            "complaint": "escalation_intent",
            "general_inquiry": "information_intent"
        }
        
        return ClassificationResult(
            category=intent_mapping.get(result.category, result.category),
            confidence=result.confidence,
            all_scores=result.all_scores
        )
