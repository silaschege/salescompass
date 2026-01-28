from django.core.exceptions import ValidationError
from products.models import ProductDependency
from .models import ProposalLine

class ConfiguratorService:
    """
    Service to handle CPQ (Configure, Price, Quote) logic.
    Enforces rules defined in ProductDependency.
    """
    
    @staticmethod
    def validate_proposal(proposal):
        """
        Validates line items against business rules.
        """
        lines = proposal.lines.all()
        products_in_proposal = [line.product for line in lines]
        errors = []
        
        for line in lines:
            primary = line.product
            # Check for mandatory dependencies
            mandatory = ProductDependency.objects.filter(
                primary_product=primary, 
                dependency_type='mandatory'
            )
            for dep in mandatory:
                if dep.dependent_product not in products_in_proposal:
                    errors.append(f"Product '{primary.product_name}' requires '{dep.dependent_product.product_name}'.")
            
            # Check for incompatibilities
            incompatible = ProductDependency.objects.filter(
                primary_product=primary, 
                dependency_type='incompatible'
            )
            for dep in incompatible:
                if dep.dependent_product in products_in_proposal:
                    errors.append(f"Product '{primary.product_name}' is incompatible with '{dep.dependent_product.product_name}'.")

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def apply_auto_rules(proposal):
        """
        Automatically adds mandatory products if they are missing.
        """
        lines = list(proposal.lines.all())
        added_any = False
        
        # We use a loop in case added products have their own dependencies
        max_iterations = 5
        for _ in range(max_iterations):
            current_products = [line.product for line in proposal.lines.all()]
            new_lines = []
            
            for line in proposal.lines.all():
                mandatory = ProductDependency.objects.filter(
                    primary_product=line.product, 
                    dependency_type='mandatory'
                )
                for dep in mandatory:
                    if dep.dependent_product not in current_products:
                        # Create new line
                        ProposalLine.objects.create(
                            proposal=proposal,
                            product=dep.dependent_product,
                            quantity=1,
                            unit_price=dep.dependent_product.base_price,
                            added_automatically=True,
                            is_required_by_another=True,
                            tenant=proposal.tenant
                        )
                        added_any = True
                        current_products.append(dep.dependent_product)
            
            if not added_any:
                break
        
        return added_any
