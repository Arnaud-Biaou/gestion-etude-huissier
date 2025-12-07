"""
Consumer WebSocket pour le chatbot.
Section 18 DSTD v3.2 - Exigence 1: "Interface WebSocket temps reel"
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatbotConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket principal pour le chatbot."""

    async def connect(self):
        """Connexion WebSocket."""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_group_name = f"chatbot_user_{self.user.id}"
        self.session_id = None

        # Joindre le groupe utilisateur
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

        # Envoyer message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_etablie',
            'message': f"Bonjour {self.user.get_short_name() or self.user.username}! Comment puis-je vous aider?",
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """Deconnexion WebSocket."""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Reception d'un message."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Format de message invalide")
            return

        message_type = data.get('type', 'message')
        contenu = data.get('contenu', '').strip()

        if not contenu:
            await self.send_error("Message vide")
            return

        # Traiter le message
        reponse = await self.traiter_message(contenu)

        await self.send(text_data=json.dumps({
            'type': 'reponse',
            'message': reponse,
            'timestamp': timezone.now().isoformat()
        }))

    async def traiter_message(self, contenu):
        """Traite un message et retourne une reponse."""
        from .nlp_processor import analyser_message
        from .permissions import verifier_permission_commande

        # Analyser le message
        analyse = analyser_message(contenu, self.user)
        intention = analyse.get('intention', 'autre')

        # Verifier les permissions RBAC
        if not await database_sync_to_async(verifier_permission_commande)(intention, self.user):
            return "Desole, vous n'avez pas les permissions necessaires pour cette action."

        # Reponses simples basees sur l'intention
        reponses = {
            'aide': "Je peux vous aider avec: la tresorerie, la comptabilite, les dossiers, les courriers et l'agenda. Que souhaitez-vous faire?",
            'tresorerie_solde': "Pour consulter le solde de tresorerie, veuillez acceder au module Tresorerie.",
            'agenda_aujourdhui': "Pour voir votre programme du jour, consultez le module Agenda.",
            'autre': "Je n'ai pas bien compris votre demande. Pouvez-vous reformuler?",
        }

        return reponses.get(intention, reponses['autre'])

    async def send_error(self, message):
        """Envoie un message d'erreur."""
        await self.send(text_data=json.dumps({
            'type': 'erreur',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))

    async def validation_completee(self, event):
        """Notification de validation completee."""
        await self.send(text_data=json.dumps({
            'type': 'validation_completee',
            'action_id': event['action_id'],
            'statut': event['statut'],
            'message': event['message'],
            'timestamp': timezone.now().isoformat()
        }))
