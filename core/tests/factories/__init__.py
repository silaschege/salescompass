# Model Factories for Testing
#
# This package contains factory-boy factories for creating test data.
# Each factory corresponds to a Django model and provides:
#   - Default values for required fields
#   - Automatic foreign key relationships
#   - Traits for common test scenarios

from tests.factories.core_factories import (
    UserFactory,
    SuperuserFactory,
)
from tests.factories.tenant_factories import (
    TenantFactory,
)
from tests.factories.accounts_factories import (
    AccountFactory,
    ContactFactory,
)
from tests.factories.leads_factories import (
    LeadFactory,
    LeadStatusFactory,
    LeadSourceFactory,
)
from tests.factories.opportunities_factories import (
    OpportunityFactory,
    OpportunityStageFactory,
)

__all__ = [
    'UserFactory',
    'SuperuserFactory',
    'TenantFactory',
    'AccountFactory',
    'ContactFactory',
    'LeadFactory',
    'LeadStatusFactory',
    'LeadSourceFactory',
    'OpportunityFactory',
    'OpportunityStageFactory',
]
