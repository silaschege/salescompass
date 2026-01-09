"""
Anomaly Service - Ontology-Based Anomaly Detection

This module provides anomaly detection services for identifying
unusual patterns in user behavior, data access, and security events.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics

from ml_models.core.ontology.base import Concept, ConceptType
from ml_models.core.knowledge_graph import KnowledgeGraph, get_knowledge_graph

logger = logging.getLogger(__name__)


class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    VOLUME = "volume"
    PATTERN = "pattern"
    SECURITY = "security"


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    score: float  # 0.0 to 1.0, higher = more anomalous
    detected_at: datetime
    entity_type: str
    entity_id: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "score": self.score,
            "detected_at": self.detected_at.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "evidence": self.evidence,
            "recommended_actions": self.recommended_actions
        }


class AnomalyService(ABC):
    """Abstract base class for anomaly detection services"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or get_knowledge_graph()
        
    @abstractmethod
    def detect(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any]
    ) -> List[Anomaly]:
        """Detect anomalies for an entity"""
        pass
    
    def calculate_severity(self, score: float) -> AnomalySeverity:
        """Calculate severity based on anomaly score"""
        if score >= 0.9:
            return AnomalySeverity.CRITICAL
        elif score >= 0.7:
            return AnomalySeverity.HIGH
        elif score >= 0.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


class PatternDetector(AnomalyService):
    """
    Detects anomalous patterns in entity behavior using
    statistical methods and ontology context.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        super().__init__(knowledge_graph)
        self.baseline_window_days = 30
        self.z_score_threshold = 2.5
        
    def detect(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any]
    ) -> List[Anomaly]:
        """
        Detect pattern anomalies.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            data: Should contain:
                - current_metrics: Dict of current metric values
                - historical_metrics: List of historical metric dicts
                - timestamp: Current timestamp
        """
        anomalies = []
        
        current_metrics = data.get("current_metrics", {})
        historical = data.get("historical_metrics", [])
        timestamp = data.get("timestamp", datetime.now())
        
        if not historical or len(historical) < 5:
            return anomalies
            
        # Analyze each metric
        for metric_name, current_value in current_metrics.items():
            if not isinstance(current_value, (int, float)):
                continue
                
            # Get historical values for this metric
            historical_values = [
                h.get(metric_name) for h in historical
                if h.get(metric_name) is not None
            ]
            
            if len(historical_values) < 5:
                continue
                
            # Calculate z-score
            mean = statistics.mean(historical_values)
            stdev = statistics.stdev(historical_values) if len(historical_values) > 1 else 1
            
            if stdev == 0:
                continue
                
            z_score = abs(current_value - mean) / stdev
            
            if z_score > self.z_score_threshold:
                score = min(z_score / 5, 1.0)  # Normalize to 0-1
                
                direction = "above" if current_value > mean else "below"
                
                anomaly = Anomaly(
                    id=f"pattern_{entity_id}_{metric_name}_{timestamp.timestamp()}",
                    anomaly_type=AnomalyType.PATTERN,
                    severity=self.calculate_severity(score),
                    title=f"Anomalous {metric_name}",
                    description=f"{metric_name} is {z_score:.1f} standard deviations {direction} normal",
                    score=score,
                    detected_at=timestamp,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    evidence={
                        "current_value": current_value,
                        "mean": mean,
                        "std_dev": stdev,
                        "z_score": z_score
                    },
                    recommended_actions=[
                        f"Investigate {metric_name} change",
                        "Review recent activities",
                        "Check for data quality issues"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def detect_trend_break(
        self,
        entity_type: str,
        entity_id: str,
        time_series: List[Tuple[datetime, float]]
    ) -> Optional[Anomaly]:
        """
        Detect if there's a sudden break in an established trend.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            time_series: List of (timestamp, value) tuples
        """
        if len(time_series) < 10:
            return None
            
        values = [v for _, v in time_series]
        
        # Simple trend detection: compare recent vs historical
        recent = values[-3:]
        historical = values[:-3]
        
        recent_avg = statistics.mean(recent)
        hist_avg = statistics.mean(historical)
        hist_std = statistics.stdev(historical) if len(historical) > 1 else 1
        
        if hist_std == 0:
            return None
            
        change_z = abs(recent_avg - hist_avg) / hist_std
        
        if change_z > 2.0:
            score = min(change_z / 4, 1.0)
            direction = "increase" if recent_avg > hist_avg else "decrease"
            
            return Anomaly(
                id=f"trend_{entity_id}_{datetime.now().timestamp()}",
                anomaly_type=AnomalyType.PATTERN,
                severity=self.calculate_severity(score),
                title="Trend Break Detected",
                description=f"Significant {direction} detected in recent values",
                score=score,
                detected_at=datetime.now(),
                entity_type=entity_type,
                entity_id=entity_id,
                evidence={
                    "recent_average": recent_avg,
                    "historical_average": hist_avg,
                    "change_magnitude": change_z
                }
            )
            
        return None


class SecurityAnomalyDetector(AnomalyService):
    """
    Detects security-related anomalies in access patterns,
    login behavior, and data access.
    """
    
    # Suspicious patterns
    SUSPICIOUS_PATTERNS = {
        "off_hours_access": {
            "description": "Access during unusual hours",
            "severity_base": 0.5
        },
        "failed_login_spike": {
            "description": "Multiple failed login attempts",
            "severity_base": 0.7
        },
        "privilege_escalation": {
            "description": "Unusual privilege changes",
            "severity_base": 0.8
        },
        "data_export_spike": {
            "description": "Unusual data export volume",
            "severity_base": 0.6
        },
        "geographic_anomaly": {
            "description": "Access from unusual location",
            "severity_base": 0.6
        },
        "api_abuse": {
            "description": "Excessive API calls",
            "severity_base": 0.5
        }
    }
    
    def detect(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any]
    ) -> List[Anomaly]:
        """
        Detect security anomalies.
        
        Args:
            entity_type: Usually "user" or "account"
            entity_id: Entity ID
            data: Security event data including:
                - login_attempts: List of login events
                - access_events: List of data access events
                - api_calls: API usage data
                - exports: Data export events
        """
        anomalies = []
        timestamp = datetime.now()
        
        # Check for failed login spikes
        login_attempts = data.get("login_attempts", [])
        failed_logins = [l for l in login_attempts if not l.get("success", True)]
        
        if len(failed_logins) >= 5:
            recent_failures = [
                l for l in failed_logins
                if self._is_recent(l.get("timestamp"), hours=1)
            ]
            
            if len(recent_failures) >= 3:
                score = min(len(recent_failures) / 10, 1.0)
                anomalies.append(self._create_security_anomaly(
                    pattern_type="failed_login_spike",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    score=score,
                    evidence={"failed_count": len(recent_failures), "window": "1 hour"}
                ))
                
        # Check for off-hours access
        access_events = data.get("access_events", [])
        off_hours_events = [
            e for e in access_events
            if self._is_off_hours(e.get("timestamp"))
        ]
        
        if off_hours_events and len(off_hours_events) / max(len(access_events), 1) > 0.3:
            score = min(len(off_hours_events) / 10, 1.0)
            anomalies.append(self._create_security_anomaly(
                pattern_type="off_hours_access",
                entity_type=entity_type,
                entity_id=entity_id,
                score=score,
                evidence={"off_hours_count": len(off_hours_events)}
            ))
            
        # Check for data export spikes
        exports = data.get("exports", [])
        recent_exports = [
            e for e in exports
            if self._is_recent(e.get("timestamp"), hours=24)
        ]
        
        if recent_exports:
            total_size = sum(e.get("size_bytes", 0) for e in recent_exports)
            if total_size > 100_000_000:  # 100MB
                score = min(total_size / 500_000_000, 1.0)
                anomalies.append(self._create_security_anomaly(
                    pattern_type="data_export_spike",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    score=score,
                    evidence={
                        "export_count": len(recent_exports),
                        "total_size_mb": total_size / 1_000_000
                    }
                ))
                
        # Check for API abuse
        api_calls = data.get("api_calls", [])
        recent_calls = [
            c for c in api_calls
            if self._is_recent(c.get("timestamp"), hours=1)
        ]
        
        if len(recent_calls) > 1000:
            score = min(len(recent_calls) / 5000, 1.0)
            anomalies.append(self._create_security_anomaly(
                pattern_type="api_abuse",
                entity_type=entity_type,
                entity_id=entity_id,
                score=score,
                evidence={"calls_per_hour": len(recent_calls)}
            ))
            
        # Update knowledge graph with detected anomalies
        self._update_knowledge_graph(entity_type, entity_id, anomalies)
        
        return anomalies
    
    def _create_security_anomaly(
        self,
        pattern_type: str,
        entity_type: str,
        entity_id: str,
        score: float,
        evidence: Dict[str, Any]
    ) -> Anomaly:
        """Create a security anomaly from a pattern type"""
        pattern = self.SUSPICIOUS_PATTERNS.get(pattern_type, {})
        adjusted_score = score * pattern.get("severity_base", 0.5)
        
        return Anomaly(
            id=f"security_{entity_id}_{pattern_type}_{datetime.now().timestamp()}",
            anomaly_type=AnomalyType.SECURITY,
            severity=self.calculate_severity(adjusted_score),
            title=pattern_type.replace("_", " ").title(),
            description=pattern.get("description", "Security anomaly detected"),
            score=adjusted_score,
            detected_at=datetime.now(),
            entity_type=entity_type,
            entity_id=entity_id,
            evidence=evidence,
            recommended_actions=self._get_recommended_actions(pattern_type)
        )
    
    def _get_recommended_actions(self, pattern_type: str) -> List[str]:
        """Get recommended actions for a pattern type"""
        actions = {
            "failed_login_spike": [
                "Verify user identity",
                "Consider temporary account lock",
                "Enable MFA if not active"
            ],
            "off_hours_access": [
                "Confirm access was authorized",
                "Review accessed resources",
                "Check for scheduled tasks"
            ],
            "data_export_spike": [
                "Review export contents",
                "Verify business justification",
                "Consider data access restrictions"
            ],
            "api_abuse": [
                "Review API usage patterns",
                "Consider rate limiting",
                "Check for automation scripts"
            ],
            "geographic_anomaly": [
                "Verify user location",
                "Check for VPN usage",
                "Review device fingerprint"
            ],
            "privilege_escalation": [
                "Audit permission changes",
                "Verify authorization",
                "Review admin activities"
            ]
        }
        return actions.get(pattern_type, ["Review and investigate"])
    
    def _is_recent(self, timestamp, hours: int = 1) -> bool:
        """Check if timestamp is within recent window"""
        if not timestamp:
            return False
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return datetime.now() - timestamp < timedelta(hours=hours)
    
    def _is_off_hours(self, timestamp) -> bool:
        """Check if timestamp is during off-hours (before 7am or after 8pm)"""
        if not timestamp:
            return False
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        hour = timestamp.hour
        return hour < 7 or hour > 20
    
    def _update_knowledge_graph(
        self,
        entity_type: str,
        entity_id: str,
        anomalies: List[Anomaly]
    ) -> None:
        """Update knowledge graph with detected anomalies"""
        if not anomalies:
            return
            
        binding = self.kg.get_entity_binding(entity_type, entity_id)
        if not binding:
            return
            
        # Add anomaly concepts to binding
        for anomaly in anomalies:
            if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                concept_id = f"anomaly_{anomaly.anomaly_type.value}"
                if concept_id not in binding.concepts:
                    binding.concepts.append(concept_id)
                    
        # Update features
        self.kg.update_entity_features(
            entity_type,
            entity_id,
            {"anomaly_count": len(anomalies)}
        )
