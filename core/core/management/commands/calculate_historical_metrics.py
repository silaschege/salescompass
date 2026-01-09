"""
Management command to calculate historical business metrics
"""
from django.core.management.base import BaseCommand
from core.services.business_metrics_service import BusinessMetricsService
from tenants.models import Tenant
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Calculate historical business metrics for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Calculate metrics for a specific tenant',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to calculate metrics for (default: 365)',
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        days = options['days']

        if tenant_id:
            # Calculate metrics for specific tenant
            self.stdout.write(f'Calculating metrics for tenant {tenant_id}')
            self.calculate_metrics_for_tenant(tenant_id, days)
        else:
            # Calculate metrics for all tenants
            tenants = Tenant.objects.all()
            for tenant in tenants:
                self.stdout.write(f'Calculating metrics for tenant {tenant.id}')
                self.calculate_metrics_for_tenant(tenant.id, days)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully calculated historical metrics for {days} days')
        )

    def calculate_metrics_for_tenant(self, tenant_id, days):
        """
        Calculate metrics for a specific tenant
        """
        # Calculate CLV metrics
        clv_metrics = BusinessMetricsService.calculate_clv_metrics(tenant_id=tenant_id)
        self.stdout.write(f'CLV Metrics for tenant {tenant_id}: {clv_metrics}')

        # Calculate CAC metrics
        cac_metrics = BusinessMetricsService.calculate_cac_metrics(tenant_id=tenant_id)
        self.stdout.write(f'CAC Metrics for tenant {tenant_id}: {cac_metrics}')

        # Calculate sales velocity metrics
        sales_velocity_metrics = BusinessMetricsService.calculate_sales_velocity_metrics(tenant_id=tenant_id)
        self.stdout.write(f'Sales Velocity Metrics for tenant {tenant_id}: {sales_velocity_metrics}')

        # Calculate ROI metrics
        roi_metrics = BusinessMetricsService.calculate_roi_metrics(tenant_id=tenant_id)
        self.stdout.write(f'ROI Metrics for tenant {tenant_id}: {roi_metrics}')

        # Calculate conversion funnel metrics
        funnel_metrics = BusinessMetricsService.calculate_conversion_funnel_metrics(tenant_id=tenant_id)
        self.stdout.write(f'Funnel Metrics for tenant {tenant_id}: {funnel_metrics}')

        # Calculate trend metrics
        trend_metrics = BusinessMetricsService.calculate_metrics_trend(days=days, tenant_id=tenant_id)
        self.stdout.write(f'Trend Metrics for tenant {tenant_id}: {len(trend_metrics["daily_metrics"])} days calculated')
