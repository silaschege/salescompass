from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


def generate_article_pdf(article_id: int) -> HttpResponse:
    """Generate PDF for an article."""
    from .models import Article, ArticleVersion
    
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
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metadata {
            color: #666;
            margin: 10px 0 20px 0;
        }
    ''')
    
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = f'attachment; filename="{article.slug}.pdf"'
    html.write_pdf(pdf_file, stylesheets=[css])
    return pdf_file