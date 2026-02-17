from elasticsearch import Elasticsearch
from django.conf import settings
from .models import Article

es = Elasticsearch([settings.ELASTICSEARCH_HOST])

def get_index_name(tenant_id=None):
    """Get Elasticsearch index name for tenant."""
    if tenant_id:
        return f"{settings.ELASTICSEARCH_INDEX_PREFIX}_{tenant_id}"
    return settings.ELASTICSEARCH_INDEX_PREFIX

def create_index(tenant_id=None):
    """Create Elasticsearch index with mapping."""
    index_name = get_index_name(tenant_id)
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text", "analyzer": "english"},
                "content": {"type": "text", "analyzer": "english"},
                "summary": {"type": "text", "analyzer": "english"},
                "tags": {"type": "keyword"},
                "article_type": {"type": "keyword"},
                "category": {"type": "keyword"},
                "tenant_id": {"type": "keyword"},
                "is_public": {"type": "boolean"},
                "status": {"type": "keyword"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping, ignore=400)

def index_article(article: Article):
    """Index an article in Elasticsearch."""
    index_name = get_index_name(article.tenant_id)
    doc = {
        "title": article.title,
        "content": article.versions.filter(is_current=True).first().content if article.versions.exists() else "",
        "summary": article.summary,
        "tags": article.get_tags_list(),
        "article_type": article.article_type,
        "category": article.category.name if article.category else "",
        "tenant_id": article.tenant_id,
        "is_public": article.is_public,
        "status": article.status,
        "article_id": article.id
    }
    es.index(index=index_name, id=article.id, body=doc)

def search_articles_elastic(query: str, tenant_id: str = None, user=None):
    """Search articles using Elasticsearch."""
    index_name = get_index_name(tenant_id)
    
    # Build query
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {"multi_match": {
                        "query": query,
                        "fields": ["title^3", "content", "summary^2", "tags"]
                    }}
                ],
                "filter": [
                    {"term": {"status": "published"}},
                    {"term": {"tenant_id": tenant_id}}
                ]
            }
        },
        "highlight": {
            "fields": {
                "content": {"fragment_size": 150, "number_of_fragments": 3},
                "summary": {"fragment_size": 150, "number_of_fragments": 1}
            }
        }
    }
    
    # Add public filter if user is not authenticated
    if user and user.is_authenticated:
        # Include public articles + tenant articles
        search_body["query"]["bool"]["filter"].append({
            "bool": {
                "should": [
                    {"term": {"is_public": True}},
                    {"term": {"tenant_id": tenant_id}}
                ]
            }
        })
    else:
        search_body["query"]["bool"]["filter"].append({"term": {"is_public": True}})
    
    response = es.search(index=index_name, body=search_body)
    return response