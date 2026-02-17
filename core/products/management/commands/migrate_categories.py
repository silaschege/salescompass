from django.core.management.base import BaseCommand
from products.models import Product, ProductCategory
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Migrate string categories to Foreign Keys'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        count = 0
        
        for product in products:
            if product.old_category:
                cat_name = product.old_category.strip()
                if not cat_name:
                    continue
                    
                # Get or Create Category
                # Note: In a real multi-tenant app, we'd need to handle tenant assignment carefully.
                # Assuming simple case or shared schema for migration.
                slug = slugify(cat_name)
                category, created = ProductCategory.objects.get_or_create(
                    name=cat_name,
                    defaults={'slug': slug}
                )
                
                # Assign
                product.category = category
                product.save()
                count += 1
                self.stdout.write(f"Migrated {product.name} -> {cat_name}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated {count} products'))
