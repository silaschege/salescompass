from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


def generate_article_pdf(article_id: int) -> HttpResponse:
    """Generate PDF for an article."""
    from .models import Article
    
    article = Article.objects.get(id=article_id)
    current_version = article.versions.filter(is_current=True).first()
    
    html_string = render_to_string('learn/export_pdf.html', {
        'article': article,
        'content': current_version.content if current_version else ""
    })
    
    html = HTML(string=html_string)
    css = CSS(string='''
        @page {
            size: letter;
            margin: 1in;
        }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }
    ''')
    
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = f'attachment; filename="{article.article_slug}.pdf"'
    html.write_pdf(pdf_file, stylesheets=[css])
    return pdf_file


def generate_certificate_pdf(certificate_id: int) -> HttpResponse:
    """Generate PDF for a course completion certificate."""
    from .models import Certificate
    
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    html_string = render_to_string('learn/certificate.html', {
        'certificate': certificate,
        'user': certificate.user,
        'course': certificate.course,
        'issue_date': certificate.issue_date
    })
    
    html = HTML(string=html_string)
    css = CSS(string='''
        @page {
            size: A4 landscape;
            margin: 0;
        }
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
        }
    ''')
    
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_number}.pdf"'
    html.write_pdf(pdf_file, stylesheets=[css])
    return pdf_file