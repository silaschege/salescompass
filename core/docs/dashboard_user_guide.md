# SalesCompass CRM - Dashboard User Guide

## Overview
The SalesCompass CRM Dashboard provides a comprehensive view of your sales pipeline, revenue trends, and recent activities. This guide will help you navigate and utilize the dashboard effectively.

## Accessing the Dashboard

### Navigation
1. Log into SalesCompass CRM
2. Click on **Dashboard** from the app selection screen, or
3. Navigate directly to `/dashboard/main/`

### User Permissions
The dashboard respects your role-based data visibility settings:
- **own_only**: See only your records
- **team_only**: See your records and your team's records
- **territory_only**: See records from your territory
- **all**: See all records (admin/executive access)

## Dashboard Components

### 1. Quick Stats Cards

Located at the top of the dashboard, these cards provide at-a-glance metrics:

#### Total Leads
- **What it shows**: Count of active leads (new, contacted, qualified statuses)
- **Change indicator**: Month-over-month percentage change
- **Color coding**: 
  - Green (+): Lead count increased
  - Red (-): Lead count decreased

#### Open Opportunities
- **What it shows**: Number of opportunities in your pipeline
- **Value display**: Total dollar value of all open opportunities
- **Use case**: Quick pipeline health check

#### Open Cases
- **What it shows**: Count of active support cases
- **Change indicator**: Trend compared to last month
- **Color coding**:
  - Green: Decreasing case count (good)
  - Red: Increasing case count (attention needed)

#### Revenue (MTD)
- **What it shows**: Month-to-date revenue from closed sales
- **Change indicator**: Comparison to last month's MTD revenue
- **Use case**: Track toward monthly revenue goals

### 2. Revenue Trend Chart

**Location**: Left side, below stats cards

**Features**:
- **Time Period**: Last 6 months of revenue data
- **Chart Type**: Line chart with gradient fill
- **Interactivity**: 
  - Hover over data points to see exact values
  - Values displayed as formatted currency (e.g., $10,000)

**How to Read**:
- **Upward trend**: Revenue is growing
- **Flat line**: Consistent revenue
- **Downward trend**: Declining revenue (investigate causes)

**Use Cases**:
- Quarterly business reviews
- Forecasting future revenue
- Identifying seasonal trends

### 3. Pipeline Snapshot

**Location**: Right side, below stats cards

**Features**:
- **Chart Type**: Horizontal bar chart
- **Data Shown**: Count of opportunities by sales stage
- **Color Coding**: Each stage has a unique color

**Stages Included**:
- Discovery
- Qualification
- Proposal
- Negotiation
- (Excludes won/lost opportunities)

**How to Read**:
- **Longer bars**: More opportunities in that stage
- **Balanced distribution**: Healthy pipeline
- **Bottlenecks**: Too many opportunities stuck in one stage

**Actions to Take**:
- If too many in early stages: Focus on qualification
- If too many in late stages: Prioritize closing deals
- If too few opportunities: Generate more leads

### 4. Recent Activity Feed

**Location**: Bottom of dashboard, full width

**Features**:
- **Limit**: Shows last 10 activities
- **Activity Types**:
  - 🔵 **Leads**: New lead captures
  - 🟢 **Opportunities**: New or updated opportunities
  - 🔴 **Cases**: New support cases

**Information Displayed**:
- **Title**: Activity type and name
- **Description**: Key details (company, amount, priority)
- **Timestamp**: Relative time (e.g., "2 hours ago")

**Use Cases**:
- Morning briefing on overnight activities
- Quick status check during the day
- Identify urgent items requiring attention

## Best Practices

### Daily Routine
1. **Morning Check** (5 minutes):
   - Review overnight activities in the feed
   - Check for urgent cases (red activities)
   - Note any large opportunities in the feed

2. **Midday Review** (10 minutes):
   - Compare current MTD revenue to target
   - Review pipeline distribution
   - Address any bottlenecks in specific stages

3. **End of Day** (5 minutes):
   - Check if any stats card trends changed
   - Plan for next day based on pipeline snapshot

### Weekly Routine
1. **Monday Planning**:
   - Review 6-month revenue trend
   - Set weekly goals based on pipeline value
   - Identify which stage needs most attention

2. **Friday Review**:
   - Compare week's stats to Monday baseline
   - Analyze which activities drove changes
   - Plan following week's priorities

### Monthly Routine
1. **Month-End Analysis**:
   - Compare final MTD revenue to target
   - Analyze 6-month trend for patterns
   - Review pipeline health for next month
   - Document lessons learned

## Interpreting Metrics

### Month-over-Month Change Percentages

**Understanding the Numbers**:
- **+50% or more**: Significant growth (investigate cause to replicate)
- **+10% to +50%**: Healthy growth
- **-10% to +10%**: Stable performance
- **-10% to -50%**: Declining (requires attention)
- **-50% or more**: Critical decline (immediate action needed)

**Context Matters**:
- Seasonal businesses may see natural fluctuations
- Compare to same period last year for better context
- Consider external factors (market conditions, holidays)

### Revenue vs. Pipeline

**Healthy Ratio**: Pipeline should be 3-5x your monthly revenue target

**Example**:
- Monthly revenue target: $100,000
- Healthy pipeline: $300,000 - $500,000
- Current pipeline: $150,000 → **Action needed**: Generate more leads

### Activity Feed Patterns

**What to Look For**:
- **Balanced mix**: Seeing leads, opportunities, and cases is normal
- **Too many cases**: May indicate product/service issues
- **No leads**: Need to increase marketing efforts
- **No opportunities**: Lead conversion issue

## Troubleshooting

### Dashboard Not Loading
1. Check your internet connection
2. Clear browser cache
3. Try a different browser
4. Contact IT support if issue persists

### Missing Data
**Possible Causes**:
- **Visibility Rules**: Your role may limit what you see
  - Contact your manager to request broader access
- **No Data**: If newly created account, data will populate as records are added
- **Filter Issues**: Check if any filters are applied

### Incorrect Numbers
**Steps to Verify**:
1. Check individual modules (Leads, Opportunities, etc.)
2. Verify your data visibility settings in Settings → Roles
3. Report discrepancy to system administrator

### Charts Not Displaying
**Browser Requirements**:
- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Ad blockers disabled (may block Chart.js CDN)

**Fix Steps**:
1. Refresh the page (F5 or Cmd+R)
2. Disable browser extensions temporarily
3. Check browser console for errors (F12)

## Mobile Access

### Responsive Design
The dashboard is optimized for mobile devices:
- **Stats cards**: Stack vertically on small screens
- **Charts**: Maintain readability with responsive sizing
- **Activity feed**: Scrollable on mobile

### Mobile Best Practices
- **Portrait mode**: Best for viewing stats and activity feed
- **Landscape mode**: Better for viewing charts
- **Tablet**: Full desktop experience

## Tips & Tricks

### Keyboard Shortcuts
- **Refresh data**: F5 or Cmd+R
- **Navigate apps**: Use browser back/forward

### Time Management
- **Set a schedule**: Check dashboard at consistent times
- **Avoid obsessing**: 2-3 checks per day is sufficient
- **Focus on trends**: Don't worry about minor daily fluctuations

### Integration with Workflow
1. **Use activity feed as task list**: Follow up on new leads immediately
2. **Pipeline snapshot for prioritization**: Focus on stages with bottlenecks
3. **Revenue trend for forecasting**: Share with leadership for planning

## Advanced Usage

### Combining with Reports
- Use dashboard for quick checks
- Use Reports module for detailed analysis
- Export data from Reports for presentations

### Team Collaboration
- Share dashboard screenshots in team meetings
- Discuss pipeline distribution strategies
- Set team goals based on collective metrics

### Performance Tracking
- Screenshot dashboard weekly for trend comparison
- Maintain a performance log
- Track correlation between activities and results

## Frequently Asked Questions

### Q: Why do my stats differ from my coworker's?
**A**: Data visibility rules filter the dashboard based on your role. You may see different data than teammates with different roles or territories.

### Q: Can I customize which metrics are shown?
**A**: Currently, the dashboard shows standard metrics. Custom dashboards may be available in future releases. Contact your administrator about custom reporting needs.

### Q: How often is data updated?
**A**: Data is real-time. Refresh your browser to see the latest updates.

### Q: Can I export dashboard data?
**A**: Use the Reports module for data export functionality. The dashboard is designed for viewing, not exporting.

### Q: Why is my revenue chart empty?
**A**: This means no sales have been recorded in the last 6 months. Create sales records in the Sales module to populate the chart.

## Support

For additional help:
- **Documentation**: Refer to module-specific guides (Leads, Opportunities, etc.)
- **In-app support**: Click the help icon (?) in the navigation bar
- **System Administrator**: Contact for role/permission issues
- **Technical Support**: For bugs or performance issues

## Appendix: Metric Definitions

### Glossary

**Active Lead**: Lead with status "new", "contacted", or "qualified"

**Open Opportunity**: Opportunity not marked as won or lost

**Open Case**: Case with status "new" or "in_progress"

**MTD Revenue**: Month-to-date revenue from closed sales

**Pipeline Value**: Sum of amounts for all open opportunities

**Sales Stage**: Current position of opportunity in sales process

**Activity**: Any create or update event on Leads, Opportunities, or Cases

---

*Last Updated: 2025-11-22*
*Version: 1.0*
