# Backward Compatibility Strategy for Dynamic Choice Models

## Overview
This document outlines the strategy for maintaining backward compatibility during the transition from hardcoded choices to dynamic choice models. The approach ensures that existing functionality continues to work while enabling the new dynamic choice capabilities.

## Strategy Components

### 1. Dual Field Approach
For each model that previously used hardcoded choices, we maintain both the old field (for backward compatibility) and the new foreign key field (for dynamic choices):

```python
class Lead(models.Model):
    # Old field - maintains existing functionality
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES)
    
    # New field - enables dynamic choices
    industry_ref = models.ForeignKey(
        Industry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='leads',
        help_text="Dynamic industry (replaces industry field)"
    )
```

### 2. Gradual Migration Path
- **Phase 1**: Add new dynamic choice fields alongside existing hardcoded choice fields
- **Phase 2**: Populate dynamic choice models with existing hardcoded values
- **Phase 3**: Migrate existing data to use new foreign key relationships
- **Phase 4**: Update application logic to prefer new dynamic fields
- **Phase 5**: Eventually deprecate and remove old hardcoded choice fields

### 3. Data Migration Process
The management command `migrate_to_dynamic_choices.py` handles the migration of existing records:

1. For each record with a hardcoded choice value, find the corresponding dynamic choice record
2. Set the new foreign key field to reference the dynamic choice
3. Maintain the old field value for backward compatibility during transition

### 4. Application Logic Updates
- Update views, forms, and business logic to check for the new dynamic field first
- Fall back to the old hardcoded field if the new field is not populated
- Example implementation pattern:

```python
def get_industry_label(self):
    if self.industry_ref:
        return self.industry_ref.label
    else:
        # Map old hardcoded value to appropriate label
        industry_map = dict(INDUSTRY_CHOICES)
        return industry_map.get(self.industry, self.industry)
```

### 5. Form Handling
- Forms should be updated to use dynamic choices when available
- Maintain support for hardcoded choices during transition period
- Example form implementation:

```python
class LeadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Use dynamic choices if available
            self.fields['industry_ref'].queryset = Industry.objects.filter(tenant_id=tenant.id)
        else:
            # Fall back to hardcoded choices
            self.fields['industry'].choices = INDUSTRY_CHOICES
```

### 6. API Compatibility
- Maintain API endpoints and response structures during transition
- Include both old and new fields in API responses where applicable
- Gradually phase out old fields as clients update

### 7. Tenant Isolation
- Each tenant has its own set of dynamic choice records
- Maintain tenant_id on all dynamic choice models for proper isolation
- Ensure migration respects tenant boundaries

### 8. Rollback Strategy
- Maintain the ability to rollback to hardcoded choices if needed
- Keep original data intact during migration
- Provide commands to reverse migration if necessary

## Implementation Timeline

### Phase 1: Model Updates (Completed)
- Added dynamic choice models
- Added new foreign key fields to existing models
- Maintained backward compatibility with old fields

### Phase 2: Data Population (Completed)
- Populated dynamic choice models with existing hardcoded values
- Created management command for initial data population

### Phase 3: Data Migration (Completed)
- Migrated existing records to use new foreign key relationships
- Created management command for data migration

### Phase 4: Application Updates (In Progress)
- Update forms to use dynamic choices
- Update views to handle dynamic choices
- Update admin interfaces
- Update business logic

### Phase 5: Testing and Validation
- Comprehensive testing of new functionality
- Validation of backward compatibility
- Performance testing with new foreign key relationships

### Phase 6: Deprecation Planning
- Plan timeline for deprecating old fields
- Update documentation
- Communicate changes to development team

## Performance Considerations

### Database Indexes
- Added indexes on foreign key fields to maintain performance
- Consider composite indexes where appropriate

### Query Optimization
- Use select_related foreign key relationships to avoid N+1 queries
- Update existing queries to leverage new relationships efficiently

## Testing Strategy

### Unit Tests
- Update existing unit tests to work with new dynamic choices
- Add tests for new dynamic choice functionality
- Ensure backward compatibility tests pass

### Integration Tests
- Test end-to-end functionality with both old and new fields
- Verify data migration works correctly
- Validate tenant isolation

### Regression Tests
- Ensure existing functionality continues to work
- Test API compatibility
- Validate form submissions and data persistence

## Monitoring and Validation

### Data Consistency Checks
- Implement checks to ensure data integrity during migration
- Monitor for orphaned records or missing relationships

### Performance Monitoring
- Track query performance after adding foreign key relationships
- Monitor application response times
- Identify and address any performance regressions

## Future Considerations

### Deprecation Path
- Plan for eventual removal of old hardcoded choice fields
- Provide migration tools for client applications
- Update API versions as needed

### Enhanced Functionality
- Leverage dynamic choices for tenant customization
- Implement choice management UI
- Add audit trails for choice changes

This strategy ensures a smooth transition to dynamic choice models while maintaining system stability and backward compatibility throughout the process.
