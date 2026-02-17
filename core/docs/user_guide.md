# SalesCompass CRM - Assignment Rule Automation User Guide

## Overview
Assignment Rule Automation allows you to automatically distribute Leads, Cases, and Opportunities to your team members based on configurable rules. This ensures that records are handled by the right person promptly, improving response times and team efficiency.

## Setting Up Assignment Rules

1.  **Navigate to Settings**: Go to the CRM Settings area.
2.  **Select Assignment Rules**: Find the "Assignment Rules" section under "Automation" or "Sales Settings".
3.  **Create a New Rule**: Click "Add Rule".
4.  **Configure Rule Details**:
    *   **Name**: Give the rule a descriptive name (e.g., "US West Tech Leads").
    *   **Module**: Select the module this rule applies to (Leads, Cases, or Opportunities).
    *   **Priority**: Set the priority (lower numbers run first). High priority rules override lower ones.
    *   **Rule Type**: Choose the assignment strategy:
        *   **Round Robin**: Distributes records evenly one-by-one to the list of assignees.
        *   **Territory-Based**: Assigns based on the record's location (e.g., Country) matching the user's territory.
        *   **Load Balanced**: Assigns to the user with the fewest active records.
        *   **Criteria-Based**: Assigns based on specific field matches (e.g., Industry = 'Technology').
5.  **Define Criteria (Optional)**:
    *   For Criteria-Based rules, define the matching logic (e.g., `{"industry": "Tech", "country": "US"}`).
6.  **Select Assignees**: Choose the users who are eligible to receive assignments under this rule.
7.  **Save**: Activate the rule.

## Troubleshooting Assignment Failures

If records are not being assigned as expected, check the following:

### 1. No Assignment Occurred
*   **Check Rule Criteria**: Ensure the record actually matches the criteria of your active rules.
*   **Check Rule Priority**: Rules are evaluated in order. A higher priority rule (lower number) might be capturing the record first.
*   **Check Assignee Availability**: Ensure the users in the rule are active and not on leave (if applicable).
*   **Check Territory Configuration**: For territory rules, ensure both the record (e.g., Lead Country) and the User's Territory are correctly configured.

### 2. Wrong User Assigned
*   **Round Robin**: This is expected behavior; the system cycles through the list.
*   **Load Balanced**: The user might have had fewer records at the exact moment of assignment.
*   **Overlapping Rules**: Multiple rules might match. The one with the highest priority (lowest number) wins.

### 3. System Issues
*   **Celery Workers**: Ensure the background task workers are running (`celery -A sCompass worker`).
*   **Redis**: Ensure the Redis broker is reachable.
*   **Logs**: Check the application logs for errors related to `evaluate_assignment_rules`.

## Support
If issues persist, please contact the system administrator or support team.
