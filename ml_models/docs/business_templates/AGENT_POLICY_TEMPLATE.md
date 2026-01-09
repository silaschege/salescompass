# Action Agent - Business Policy Template

Use this template to define how AI Agents should react to ML insights. Once filled, these rules can be configured in the `infrastructure/config/` templates.

## Agent: Lead Nurture Agent

### Outreach Rules
| Condition (ML Score) | Business Action | Priority |
| :--- | :--- | :--- |
| **Score >= 90** | Trigger Slack Alert to Rep + Manager | High |
| **Score >= 75** | Auto-Send "Personalized Demo" Email | Medium |
| **Score >= 60** | Schedule "Follow-up Task" for 48h | Medium |
| **Score < 50** | Add to "Low Touch" Marketing List | Low |

---

## Agent: Opportunity Assistant

### Pipeline Hygiene Rules
| Condition | Business Action | Priority |
| :--- | :--- | :--- |
| **Win Prob < 20%** (Deal > $10k) | Alert Sales VP for "Deal Rescue" | High |
| **No Activity > 7 Days** | Flag Opportunity as "Stagnant" | Medium |
| **Win Prob > 80%** | Notify Finance for "Revenue Forecasting" | High |

---

## Instructions for Managers
1.  **Define your thresholds**: Work with your Data Science team to see where the "sweet spot" is for conversion.
2.  **Select your channels**: Choose where alerts should go (Email, SMS, CRM Task, Slack).
3.  **Review Performance**: Every month, review the "Action Log" to see if these automated steps are helping your team close more deals.
