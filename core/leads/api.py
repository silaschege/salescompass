from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from core.models import TenantModel
from .models import Lead
from .services import LeadScoringService

class WebToLeadView(APIView):
    """
    Public API endpoint for capturing leads from external websites.
    Requires a valid API Key (Tenant ID) in the header or payload.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        
        # 1. Authentication/Tenant Identification
        # Expecting 'X-Tenant-ID' header or 'tenant_id' in body
        tenant_id = request.headers.get('X-Tenant-ID') or data.get('tenant_id')
        
        if not tenant_id:
            return Response(
                {"error": "Missing Tenant ID. Please provide X-Tenant-ID header or tenant_id field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Validation
        required_fields = ['first_name', 'last_name', 'email']
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Create Lead
        try:
            lead = Lead.objects.create(
                tenant_id=tenant_id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data.get('phone', ''),
                company=data.get('company', ''),
                job_title=data.get('job_title', ''),
                source=data.get('source', 'Web Form'),
                status='new',
                notes=data.get('message', '')  # Map 'message' form field to notes
            )
            
            # 4. Trigger Intelligence (Scoring)
            LeadScoringService.calculate_lead_score(lead)
            
            return Response(
                {"success": True, "lead_id": lead.id, "message": "Lead captured successfully"},
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
