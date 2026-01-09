from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
def dashboard(request):
    """
    Developer portal dashboard showing API documentation and developer tools.
    """
    context = {
        'page_title': 'Developer Portal',
        'api_docs_url': '/api/docs/',
        'redoc_url': '/api/redoc/',
        'schema_url': '/api/schema/',
    }
    return render(request, 'developer/dashboard.html', context)


@login_required
def portal(request):
    """
    Comprehensive developer portal with API key management, usage stats, and tools.
    """
    from .models import APIToken as APIKey, Webhook  # Both from developer app
    
    # Get user's API keys (actually APIToken objects)
    api_keys = APIKey.objects.filter(
        user=request.user,
        tenant=request.user.tenant
    ).order_by('-created_at')
    
    # Get webhooks
    webhooks = Webhook.objects.filter(
        tenant=request.user.tenant
    ).order_by('-created_at')
    
    # Calculate usage statistics
    total_api_calls = sum(1 for key in api_keys if key.last_used_at is not None)
    total_webhooks = webhooks.count()
    successful_webhooks = sum(getattr(w, 'success_count', 0) for w in webhooks)
    failed_webhooks = sum(getattr(w, 'failure_count', 0) for w in webhooks)
    
    context = {
        'page_title': 'Developer Portal',
        'api_keys': api_keys,
        'webhooks': webhooks,
        'stats': {
            'total_api_keys': api_keys.count(),
            'active_api_keys': api_keys.filter(is_active=True).count(),
            'total_webhooks': total_webhooks,
            'successful_webhooks': successful_webhooks,
            'failed_webhooks': failed_webhooks,
        },
        'base_url': f"{request.scheme}://{request.get_host()}",
    }
    return render(request, 'developer/portal.html', context)

@login_required
@require_POST
def generate_api_key(request):
    """
    Generate a new API key for the user.
    """
    from .models import APIToken as APIKey  # From developer app
    
    name = request.POST.get('name', 'API Key')
    scopes = request.POST.getlist('scopes', ['read'])
    
    # Generate the key
    import secrets
    token = f"sk_live_{secrets.token_urlsafe(32)}"
    
    # Create the API key object (actually APIToken)
    api_key = APIKey.objects.create(
        name=name,
        token=token,
        user=request.user,
        tenant=request.user.tenant,
        scopes=scopes
    )
    
    messages.success(request, f'API key "{name}" created successfully! Save this token: {token}')
    return redirect('developer:portal')



@login_required
def usage_analytics(request):
    """
    Display usage analytics for API keys and webhooks.
    """
    from .models import APIToken as APIKey, Webhook  # Both from developer app
    from django.db.models import Count, Sum
    
    # Get API key usage
    api_keys = APIKey.objects.filter(
        user=request.user,
        tenant=request.user.tenant
    ).order_by('-last_used_at')
    
    # Get webhook statistics
    webhooks = Webhook.objects.filter(
        tenant=request.user.tenant
    )
    
    webhook_stats = {
        'total': webhooks.count(),
        'active': webhooks.filter(is_active=True).count(),
        'total_success': sum(getattr(w, 'success_count', 0) for w in webhooks),
        'total_failures': sum(getattr(w, 'failure_count', 0) for w in webhooks),
    }
    
    context = {
        'page_title': 'Usage Analytics',
        'api_keys': api_keys,
        'webhook_stats': webhook_stats,
        'webhooks': webhooks,
    }
    return render(request, 'developer/analytics.html', context)




@login_required
@require_POST
def test_webhook(request):
    """
    Test a webhook by sending a sample payload.
    """
    from .models import Webhook  # From developer app
    from .task import deliver_webhook  # Use developer app's task
    
    webhook_id = request.POST.get('webhook_id')
    event_type = request.POST.get('event_type', 'test.event')
    
    # Validate webhook ID
    if not webhook_id:
        return JsonResponse({
            'success': False,
            'error': 'Webhook ID is required'
        }, status=400)
    
    # Check if webhook exists
    try:
        webhook = Webhook.objects.get(id=int(webhook_id), tenant=request.user.tenant)
    except (Webhook.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Webhook not found'
        }, status=400)
    
    # Sample payload
    payload = {
        'test': True,
        'message': 'This is a test webhook delivery',
        'timestamp': '2024-01-01T00:00:00Z'
    }
    
    try:
        # Queue the webhook delivery
        deliver_webhook.delay(int(webhook_id), event_type, payload)
        return JsonResponse({
            'success': True,
            'message': 'Webhook test queued successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)



@login_required
def api_keys(request):
    """
    View for managing API keys.
    """
    from .models import APIToken as APIKey  # From developer app
    
    api_keys = APIKey.objects.filter(
        user=request.user,
        tenant=request.user.tenant
    ).order_by('-created_at')
    
    context = {
        'page_title': 'API Keys',
        'api_keys': api_keys,
    }
    return render(request, 'developer/api_keys.html', context)

@login_required
def webhooks(request):
    """
    View for managing webhooks.
    """
    from .models import Webhook  # From developer app
    
    webhooks = Webhook.objects.filter(
        tenant=request.user.tenant
    ).order_by('-created_at')
    
    context = {
        'page_title': 'Webhooks',
        'webhooks': webhooks,
    }
    return render(request, 'developer/webhooks.html', context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from .models import APIToken, Webhook
import calendar
from collections import defaultdict

@login_required
def monitoring_dashboard(request):
    """
    Main monitoring dashboard showing API usage, error rates, latency, and quotas.
    """
    tenant = request.user.tenant
    
    # Get time range for analysis (last 7 days)
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=7)
    
    # API Usage analytics
    api_tokens = APIToken.objects.filter(tenant=tenant)
    total_requests = sum(token.daily_request_count for token in api_tokens)
    
    # Webhook statistics
    webhooks = Webhook.objects.filter(tenant=tenant)
    total_webhooks = webhooks.count()
    successful_webhooks = sum(w.success_count for w in webhooks)
    failed_webhooks = sum(w.failure_count for w in webhooks)
    total_deliveries = successful_webhooks + failed_webhooks
    
    # Calculate error rate
    error_rate = (failed_webhooks / total_deliveries * 100) if total_deliveries else 0
    
    # Latency statistics
    avg_latency = sum(w.avg_delivery_time_ms for w in webhooks) / total_webhooks if total_webhooks else 0
    
    # Quota usage
    quota_usage = [(token.name, token.daily_request_count, token.rate_limit) for token in api_tokens]
    
    context = {
        'page_title': 'Monitoring Dashboard',
        'api_usage': {
            'total_requests': total_requests,
            'daily_avg': total_requests / 7,  # Assuming weekly data
            'active_tokens': api_tokens.filter(is_active=True).count(),
        },
        'error_rate': error_rate,
        'latency': {
            'avg': avg_latency,
            'p95': sum(w.p95_delivery_time_ms for w in webhooks) / total_webhooks if total_webhooks else 0,
            'p99': sum(w.p99_delivery_time_ms for w in webhooks) / total_webhooks if total_webhooks else 0,
        },
        'quota_usage': quota_usage,
        'time_range': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    }
    
    return render(request, 'developer/monitoring_dashboard.html', context)


@login_required
def api_usage_chart(request):
    """
    API usage chart data for the dashboard.
    Returns JSON data for the past 7 days.
    """
    tenant = request.user.tenant
    end_date = timezone.now()
    
    # Get daily request counts for the past 7 days
    daily_counts = []
    for i in range(7):
        date = end_date - timezone.timedelta(days=i)
        next_date = date + timezone.timedelta(days=1)
        
        count = APIToken.objects.filter(tenant=tenant).aggregate(
            total=Sum('daily_request_count')
        )['total'] or 0
        
        daily_counts.append({
            'date': date.strftime('%Y-%m-%d'),
            'requests': count
        })
    
    # Reverse to have oldest first
    daily_counts.reverse()
    
    return JsonResponse(daily_counts, safe=False)


@login_required
def webhook_stats_chart(request):
    """
    Webhook statistics chart data for the dashboard.
    Returns JSON data for the past 7 days.
    """
    tenant = request.user.tenant
    end_date = timezone.now()
    
    # Get daily webhook stats for the past 7 days
    daily_stats = []
    for i in range(7):
        date = end_date - timezone.timedelta(days=i)
        next_date = date + timezone.timedelta(days=1)
        
        successes = Webhook.objects.filter(tenant=tenant).aggregate(
            total=Sum('success_count')
        )['total'] or 0
        
        failures = Webhook.objects.filter(tenant=tenant).aggregate(
            total=Sum('failure_count')
        )['total'] or 0
        
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'successes': successes,
            'failures': failures
        })
    
    # Reverse to have oldest first
    daily_stats.reverse()
    
    return JsonResponse(daily_stats, safe=False)


@login_required
def quota_alerts(request):
    """
    View for managing quota alerts.
    """
    tenant = request.user.tenant
    
    # Get API tokens that are close to their quota
    threshold = 0.8  # 80% threshold
    high_usage_tokens = []
    
    for token in APIToken.objects.filter(tenant=tenant, is_active=True):
        if token.daily_request_count > token.rate_limit * threshold:
            high_usage_tokens.append({
                'token': token,
                'usage_percent': (token.daily_request_count / token.rate_limit) * 100
            })
    
    context = {
        'page_title': 'Quota Alerts',
        'high_usage_tokens': high_usage_tokens,
        'threshold': threshold * 100
    }
    
    return render(request, 'developer/quota_alerts.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required



@login_required
def documentation(request):
    """
    View for API documentation
    """
    context = {
        'page_title': 'API Documentation',
    }
    return render(request, 'developer/documentation.html', context)

@login_required
def api_explorer(request):
    """
    View for API request/response examples
    """
    context = {
        'page_title': 'API Explorer',
    }
    return render(request, 'developer/api_explorer.html', context)
