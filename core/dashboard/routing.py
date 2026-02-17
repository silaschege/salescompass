from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/bi_dashboard/<int:tenant_id>/", consumers.BIDashboardConsumer.as_asgi()),
]
