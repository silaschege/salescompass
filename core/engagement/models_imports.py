from django.db import models
from tenants.models import TenantAwareModel as TenantModel
from core.models import User, TimeStampedModel
from opportunities.models import Opportunity
from django.utils import timezone
