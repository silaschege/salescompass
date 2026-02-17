# Explainable AI (XAI) - Interpretation Template

This template defines how complex technical model explanations (like SHAP values) are translated into clear, human-readable reasons for sales reps.

## Technical-to-Business Mapping

| Technical Feature | Positive Impact Language (+) | Negative Impact Language (-) |
| :--- | :--- | :--- |
| **Days Since Interaction** | "Engaged with lead within the last 24 hours." | "No engagement for over 7 days." |
| **Profile Completeness** | "Comprehensive profile with industry and revenue data." | "Missing critical contact or industry data." |
| **Website Visits** | "Frequent website activity indicates high interest." | "Low digital engagement recently." |
| **Lead Source: Event** | "Met at high-impact industry trade show." | "Cold web-form acquisition." |
| **Opp Stage Velocity** | "Moving through sale stages faster than average." | "Stalling in the discovery phase." |

## User Interface (UI) Presentation
When displaying reasons in the CRM dashboard, follow this layout:

> **AI Summary**: This lead has a **Hot** score (94).
> 
> **Top Positive Drivers**:
> - ✅ Recently Met at industry trade show.
> - ✅ Profile is 100% complete.
> 
> **Top Negative Drivers**:
> - ⚠️ No direct interaction for 3 days.
> 
> **Recommendation**: Trigger high-priority outreach immediately.

## Customization Guide
Reps can add "Custom Feedback" at the bottom of the insight widget if they disagree with the AI's reason. This feedback is used to further refine the AI's logic.
