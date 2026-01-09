import sys
import os
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Opportunity, ForecastSnapshot, WinLossAnalysis
from django.http import JsonResponse
from django.db.models import Case, When, FloatField, Sum, F, Count
from django.shortcuts import get_object_or_404
import json
from django.db.models import Avg

from infrastructure.ml_client import ml_client

def calculate_weighted_forecast(tenant_id: str = None) -> dict:
    """
    Compute total pipeline and weighted forecast using ML module API.
    """
    # Filter for open opportunities
    queryset = Opportunity.objects.filter(
        stage__is_won=False,
        stage__is_lost=False
    )
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
        
    # Prepare data for API
    opp_data = [
        {'amount': float(opp.amount), 'probability': float(opp.probability or 0.0)}
        for opp in queryset
    ]
    
    result = ml_client.predict_revenue_forecast(opp_data)
    
    return {
        'total_pipeline': result['forecast_amount'],
        'weighted_forecast': result['weighted_forecast_amount'],
    }


def create_forecast_snapshot(tenant_id: str = None) -> ForecastSnapshot:
    """
    Create a daily snapshot for historical reporting.
    """
    data = calculate_weighted_forecast(tenant_id)
    return ForecastSnapshot.objects.create(
        date=timezone.now().date(),
        total_pipeline_value=data['total_pipeline'],
        weighted_forecast=data['weighted_forecast'],
        tenant_id=tenant_id
    )


def calculate_forecast_accuracy(tenant_id: str = None) -> dict:
    """
    Calculate forecast accuracy (MAPE) for the last 30 days.
    """
    # Compare forecast from 30 days ago vs Actuals closed since then
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    old_snapshot = ForecastSnapshot.objects.filter(
        tenant_id=tenant_id,
        date=thirty_days_ago
    ).first()

    if not old_snapshot:
        return {'accuracy': None, 'mape': None}

    # Get opportunities closed in the last 30 days
    recent_won_opps = Opportunity.objects.filter(
        tenant_id=tenant_id,
        stage__is_won=True,
        close_date__gte=thirty_days_ago
    )

    actual_revenue = sum(float(opp.amount) for opp in recent_won_opps)

    # MAPE calculation
    if old_snapshot.weighted_forecast > 0:
        mape = abs(actual_revenue - float(old_snapshot.weighted_forecast)) / actual_revenue * 100
        return {
            'accuracy': 100 - mape,
            'mape': mape,
            'actual_revenue': actual_revenue,
            'predicted_revenue': float(old_snapshot.weighted_forecast)
        }

    return {'accuracy': None, 'mape': None}


def check_forecast_alerts(tenant_id: str = None) -> list:
    """
    Check for forecast-related alerts.
    """
    alerts = []

    # Get recent snapshots for trend analysis
    recent_snapshots = ForecastSnapshot.objects.filter(
        tenant_id=tenant_id
    ).order_by('-date')[:7]  # Last 7 days

    if len(recent_snapshots) >= 2:
        current = recent_snapshots[0]
        previous = recent_snapshots[1]

        # Check for significant drops in forecast (more than 10%)
        if previous.weighted_forecast > 0:
            change_percent = (
                (float(current.weighted_forecast) - float(previous.weighted_forecast)) /
                float(previous.weighted_forecast) * 100
            )

            if change_percent < -10:  # More than 10% drop
                alerts.append({
                    'type': 'forecast_drop',
                    'message': f'Forecast dropped {abs(change_percent):.1f}% compared to yesterday',
                    'severity': 'warning'
                })

    return alerts


def get_win_loss_stats(tenant_id: str = None) -> dict:
    """
    Get win/loss statistics for opportunities.
    """
    queryset = Opportunity.objects.all()
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)

    total_count = queryset.count()
    won_count = queryset.filter(stage__is_won=True).count()
    lost_count = queryset.filter(stage__is_lost=True).count()

    # Calculate win rate
    win_rate = (won_count / total_count * 100) if total_count > 0 else 0

    # Average deal size for won vs lost
    avg_won_size = queryset.filter(stage__is_won=True).aggregate(
        avg=Avg('amount')
    )['avg'] or 0

    avg_lost_size = queryset.filter(stage__is_lost=True).aggregate(
        avg=Avg('amount')
    )['avg'] or 0

    return {
        'total_count': total_count,
        'won_count': won_count,
        'lost_count': lost_count,
        'win_rate': win_rate,
        'avg_won_size': float(avg_won_size),
        'avg_lost_size': float(avg_lost_size)
    }