import csv
from io import StringIO
from typing import List, Dict, Tuple
from django.core.exceptions import ValidationError
from core.models import User

INDUSTRY_CHOICES = {choice[0] for choice in [
    ('tech', 'Technology'),
    ('manufacturing', 'Manufacturing'),
    ('finance', 'Finance'),
    ('healthcare', 'Healthcare'),
    ('retail', 'Retail'),
    ('energy', 'Energy'),
    ('education', 'Education'),
    ('other', 'Other'),
]}

TIER_CHOICES = {'bronze', 'silver', 'gold', 'platinum'}
ESG_CHOICES = {'low', 'medium', 'high'}

def parse_accounts_csv(file, user) -> Tuple[List[Dict], List[str]]:
    """
    Parse CSV and return list of row dicts + list of errors.
    User is used to scope account visibility (for bulk import validation).
    """
    errors = []
    rows = []

    # Read file
    if hasattr(file, 'read'):
        content = file.read().decode('utf-8')
    else:
        content = file

    reader = csv.DictReader(StringIO(content))
    headers = reader.fieldnames or []

    # Validate headers
    REQUIRED_FIELDS = {'name', 'industry', 'country'}
    ALLOWED_FIELDS = REQUIRED_FIELDS | {
        'tier', 'website', 'address', 'esg_engagement', 'sustainability_goals',
        'renewal_date', 'gdpr_consent', 'ccpa_consent'
    }

    missing_required = REQUIRED_FIELDS - set(headers)
    if missing_required:
        errors.append(f"Missing required columns: {', '.join(missing_required)}")
        return rows, errors

    unknown_fields = set(headers) - ALLOWED_FIELDS
    if unknown_fields:
        errors.append(f"Unknown columns (ignored): {', '.join(unknown_fields)}")

    # Parse rows
    for i, row in enumerate(reader, start=2):
        try:
            cleaned_row = _clean_row(row, i)
            rows.append(cleaned_row)
        except ValidationError as e:
            errors.append(f"Row {i}: {e.message}")
        except Exception as e:
            errors.append(f"Row {i}: Unexpected error: {str(e)}")

    return rows, errors


def _clean_row(row: Dict[str, str], row_num: int) -> Dict[str, any]:
    """Clean and validate a single row."""
    cleaned = {}

    # Required fields
    for field in ['name', 'industry', 'country']:
        value = row.get(field, '').strip()
        if not value:
            raise ValidationError(f"'{field}' is required")
        cleaned[field] = value

    # Optional fields with validation
    if 'tier' in row:
        tier = row['tier'].strip().lower()
        if tier and tier not in TIER_CHOICES:
            raise ValidationError(f"Invalid tier: {tier}. Must be one of: {', '.join(TIER_CHOICES)}")
        cleaned['tier'] = tier or 'bronze'

    if 'industry' in cleaned:
        industry = cleaned['industry'].lower()
        if industry not in INDUSTRY_CHOICES:
            raise ValidationError(f"Invalid industry: {industry}")
        cleaned['industry'] = industry

    if 'esg_engagement' in row:
        esg = row['esg_engagement'].strip().lower()
        if esg and esg not in ESG_CHOICES:
            raise ValidationError(f"Invalid ESG engagement: {esg}. Must be low/medium/high")
        cleaned['esg_engagement'] = esg or 'low'

    # Boolean fields
    for bool_field in ['gdpr_consent', 'ccpa_consent']:
        if bool_field in row:
            val = row[bool_field].strip().lower()
            cleaned[bool_field] = val in ('true', '1', 'yes', 'on')

    # Date field
    if 'renewal_date' in row and row['renewal_date'].strip():
        from datetime import datetime
        try:
            datetime.strptime(row['renewal_date'].strip(), '%Y-%m-%d')
            cleaned['renewal_date'] = row['renewal_date'].strip()
        except ValueError:
            raise ValidationError("Invalid renewal_date format. Use YYYY-MM-DD")

    return cleaned

def pprint(value):
    """Pretty print JSON/dict for templates."""
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    return str(value)