"""
Configuration du routage WebSocket pour le chatbot.
Section 18 DSTD v3.2 - Exigence 1: "Interface WebSocket temps reel"
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chatbot/$', consumers.ChatbotConsumer.as_asgi()),
]
