import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Proposal, ProposalEvent, ProposalEmail, ProposalPDF

def record_proposal_view(proposal_id: int, ip: str = None, user_agent: str = None) -> None:
    """Record a proposal view and update engagement metrics."""
    proposal = Proposal.objects.select_for_update().get(id=proposal_id)
    
    # Update proposal
    proposal.view_count += 1
    proposal.last_viewed = timezone.now()
    proposal.save(update_fields=['view_count', 'last_viewed'])

    # Create event
    ProposalEvent.objects.create(
        proposal=proposal,
        event_type='opened',
        ip_address=ip,
        user_agent=user_agent
    )

    # Emit event for automation
    from automation.utils import emit_event
    emit_event('proposal.viewed', {
        'proposal_id': proposal.id,
        'account_id': proposal.opportunity.account_id,
        'tenant_id': proposal.tenant_id,
    })


def record_esg_view(proposal_id: int) -> None:
    """Record ESG section view."""
    proposal = Proposal.objects.select_for_update().get(id=proposal_id)
    if not proposal.esg_section_viewed:
        proposal.esg_section_viewed = True
        proposal.save(update_fields=['esg_section_viewed'])
        
        ProposalEvent.objects.create(
            proposal=proposal,
            event_type='esg_viewed'
        )

        # Emit event for ESG automation
        from automation.utils import emit_event
        emit_event('proposal.esg_viewed', {
            'proposal_id': proposal.id,
            'account_id': proposal.opportunity.account_id,
            'tenant_id': proposal.tenant_id,
        })


def send_proposal_email(proposal_id: int, recipient_email: str, user=None) -> ProposalEmail:
    """Send proposal email with tracking."""
    proposal = Proposal.objects.get(id=proposal_id)
    
    # Create tracking tokens
    open_token = str(uuid.uuid4())
    click_token = str(uuid.uuid4())
    
    # Create email record
    email_record = ProposalEmail.objects.create(
        proposal=proposal,
        recipient_email=recipient_email,
        subject=f"Proposal: {proposal.title}",
        open_tracking_token=open_token,
        click_tracking_token=click_token,
        tenant_id=proposal.tenant_id
    )
    
    # Render email with tracking
    html_content = render_to_string('proposals/email_template.html', {
        'proposal': proposal,
        'open_token': open_token,
        'click_token': click_token,
        'recipient_email': recipient_email
    })
    
    # Send email
    msg = EmailMultiAlternatives(
        subject=email_record.subject,
        body="Please view in HTML",
        from_email="proposals@salescompass.com",
        to=[recipient_email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
    # Update proposal status
    proposal.status = 'sent'
    proposal.sent_by = user
    proposal.save(update_fields=['status', 'sent_by'])
    
    email_record.sent_at = timezone.now()
    email_record.save(update_fields=['sent_at'])
    
    return email_record


def generate_proposal_pdf(proposal_id: int, user=None) -> ProposalPDF:
    """Generate PDF from proposal."""
    from django.template.loader import render_to_string
    from weasyprint import HTML, CSS
    from io import BytesIO
    import os
    
    proposal = Proposal.objects.get(id=proposal_id)
    html_string = render_to_string('proposals/proposal_pdf.html', {'proposal': proposal})
    
    html = HTML(string=html_string)
    css = CSS(string='''
        @page { size: letter; margin: 1in; }
        body { font-family: Arial, sans-serif; line-height: 1.4; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
        .esg-box { background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 15px; margin: 20px 0; }
    ''')
    
    pdf_file = BytesIO()
    html.write_pdf(pdf_file, stylesheets=[css])
    pdf_file.seek(0)
    
    # Save to model
    pdf_record = ProposalPDF.objects.create(
        proposal=proposal,
        generated_by=user,
        tenant_id=proposal.tenant_id
    )
    pdf_record.file.save(f"proposal_{proposal_id}.pdf", pdf_file)
    
    # Create event
    ProposalEvent.objects.create(
        proposal=proposal,
        event_type='downloaded'
    )
    
    return pdf_record


def track_email_open(email_token: str) -> None:
    """Track email open via pixel."""
    try:
        email_record = ProposalEmail.objects.get(open_tracking_token=email_token)
        
        if not email_record.opened_at:
            email_record.opened_at = timezone.now()
        
        email_record.opened_count += 1
        email_record.save(update_fields=['opened_at', 'opened_count'])
        
        # Update proposal
        proposal = email_record.proposal
        proposal.email_opened = True
        proposal.email_opened_at = email_record.opened_at
        proposal.save(update_fields=['email_opened', 'email_opened_at'])
        
        # Create event
        ProposalEvent.objects.create(
            proposal=proposal,
            event_type='email_opened'
        )
        
    except ProposalEmail.DoesNotExist:
        pass


def track_link_click(click_token: str, url: str) -> str:
    """Track link click and redirect."""
    try:
        email_record = ProposalEmail.objects.get(click_tracking_token=click_token)
        email_record.clicked_count += 1
        email_record.save(update_fields=['clicked_count'])
        
        # Update proposal
        proposal = email_record.proposal
        proposal.email_click_count = email_record.clicked_count
        proposal.save(update_fields=['email_click_count'])
        
        # Create event
        ProposalEvent.objects.create(
            proposal=proposal,
            event_type='link_clicked',
            link_url=url
        )
    except ProposalEmail.DoesNotExist:
        pass
    
    return url