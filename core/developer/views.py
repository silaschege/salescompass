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
    from settings_app.models import APIKey, Webhook
    
    # Get user's API keys
    api_keys = APIKey.objects.filter(
        created_by=request.user,
        tenant_id=request.user.tenant_id
    ).order_by('-created_at')
    
    # Get webhooks
    webhooks = Webhook.objects.filter(
        tenant_id=request.user.tenant_id
    ).order_by('-created_at')
    
    # Calculate usage statistics
    total_api_calls = sum(key.last_used is not None for key in api_keys)
    total_webhooks = webhooks.count()
    successful_webhooks = sum(w.success_count for w in webhooks)
    failed_webhooks = sum(w.failure_count for w in webhooks)
    
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
    from settings_app.models import APIKey
    
    name = request.POST.get('name', 'API Key')
    scopes = request.POST.getlist('scopes', ['read'])
    
    # Generate the key
    key = APIKey.generate_key()
    
    # Create the API key object
    api_key = APIKey.objects.create(
        name=name,
        scopes=scopes,
        created_by=request.user,
        tenant_id=request.user.tenant_id
    )
    api_key.set_key(key)
    api_key.save()
    
    messages.success(request, f'API key "{name}" created successfully! Save this key: {key}')
    return redirect('developer:portal')

@login_required
def usage_analytics(request):
    """
    Display usage analytics for API keys and webhooks.
    """
    from settings_app.models import APIKey, Webhook
    from django.db.models import Count, Sum
    
    # Get API key usage
    api_keys = APIKey.objects.filter(
        created_by=request.user,
        tenant_id=request.user.tenant_id
    ).order_by('-last_used')
    
    # Get webhook statistics
    webhooks = Webhook.objects.filter(
        tenant_id=request.user.tenant_id
    )
    
    webhook_stats = {
        'total': webhooks.count(),
        'active': webhooks.filter(is_active=True).count(),
        'total_success': sum(w.success_count for w in webhooks),
        'total_failures': sum(w.failure_count for w in webhooks),
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
    from settings_app.models import Webhook
    from settings_app.tasks import deliver_webhook
    
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
        webhook = Webhook.objects.get(id=int(webhook_id), tenant_id=request.user.tenant_id)
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
    from settings_app.models import APIKey
    
    api_keys = APIKey.objects.filter(
        created_by=request.user,
        tenant_id=request.user.tenant_id
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
    from settings_app.models import Webhook
    
    webhooks = Webhook.objects.filter(
        tenant_id=request.user.tenant_id
    ).order_by('-created_at')
    
    context = {
        'page_title': 'Webhooks',
        'webhooks': webhooks,
    }
    return render(request, 'developer/webhooks.html', context)
