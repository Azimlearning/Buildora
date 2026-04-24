"""
Agent D — Notifications & Alerts
=================================
Receives alerts from Agent B and dispatches them to the UI (Firestore)
and to the Project Manager's Telegram chat.

Author: Khaidhir
"""

from backend.agents.agent_d.agent import AgentD
from backend.agents.agent_d.telegram_notifier import TelegramNotifier

__all__ = ["AgentD", "TelegramNotifier"]
