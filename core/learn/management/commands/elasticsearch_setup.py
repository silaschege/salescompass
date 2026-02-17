from django.core.management.base import BaseCommand
from django.conf import settings
from apps.learn.search import create_index, index_article
from apps.learn.models import Article

class Command(BaseCommand):
    help = 'Setup Elasticsearch indices and reindex all articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant ID to setup (setup all tenants if not specified)'
        )
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='Reindex all articles after creating indices'
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant']
        reindex = options['reindex']
        
        if tenant_id:
            # Setup specific tenant
            self.stdout.write(f'Setting up Elasticsearch for tenant: {tenant_id}')
            if create_index(tenant_id):
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created index for tenant {tenant_id}')
                )
                
                if reindex:
                    self.reindex_articles(tenant_id)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create index for tenant {tenant_id}')
                )
        else:
            # Setup all tenants
            self.stdout.write('Setting up Elasticsearch for all tenants')
            
            # Get all unique tenant_ids from articles
            tenant_ids = Article.objects.values_list('tenant_id', flat=True).distinct()
            
            for tid in tenant_ids:
                if create_index(tid):
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully created index for tenant {tid}')
                    )
                    
                    if reindex:
                        self.reindex_articles(tid)
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to create index for tenant {tid}')
                    )
            
            # Also create default index
            if create_index():
                self.stdout.write(
                    self.style.SUCCESS('Successfully created default index')
                )
                
                if reindex:
                    # Reindex articles without tenant_id
                    articles = Article.objects.filter(tenant_id__isnull=True)
                    for article in articles:
                        if index_article(article):
                            self.stdout.write(f'Indexed article: {article.title}')
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'Failed to index article: {article.title}')
                            )

    def reindex_articles(self, tenant_id):
        """Reindex all articles for a tenant."""
        if tenant_id:
            articles = Article.objects.filter(tenant_id=tenant_id, status='published')
        else:
            articles = Article.objects.filter(tenant_id__isnull=True, status='published')
            
        self.stdout.write(f'Reindexing {articles.count()} articles for tenant {tenant_id or "default"}')
        
        for article in articles:
            if index_article(article):
                self.stdout.write(f'Indexed article: {article.title}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to index article: {article.title}')
                )