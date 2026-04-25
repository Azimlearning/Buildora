"""
Telegram Notifier for Agent D
==============================
Sends formatted alert messages to the Project Manager's Telegram chat.

Uses the Telegram Bot API via httpx (async HTTP).
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the application settings.

Alert categories handled:
  - doc_submission   → Document submission deadlines
  - payment_due      → Payment deadlines
  - account_receivable → Outstanding receivables
  - extension_of_time → EOT notices / approvals
  - delay_detected   → Schedule delay flags (from Agent B)
  - cost_overrun     → Cost variance flags (from Agent B)
  - permit_renewal   → Permit / license renewals
  - general          → Catch-all

Author: Khaidhir (Agent D)
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Emoji map per alert category ──────────────────────────────────
CATEGORY_EMOJI = {
    "doc_submission":     "📄",
    "payment_due":        "💰",
    "account_receivable": "🧾",
    "extension_of_time":  "⏳",
    "delay_detected":     "🚨",
    "cost_overrun":       "📊",
    "permit_renewal":     "🪪",
    "general":            "🔔",
}

# ── Severity labels ───────────────────────────────────────────────
SEVERITY_LABEL = {
    "critical": "🔴 CRITICAL",
    "high":     "🟠 HIGH",
    "medium":   "🟡 MEDIUM",
    "low":      "🟢 LOW",
    "info":     "ℹ️ INFO",
}


class TelegramNotifier:
    """
    Async Telegram Bot API client for dispatching project alerts.
    """

    SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Args:
            bot_token: Telegram bot token.  Falls back to settings if None.
            chat_id:   Default chat to send to.  Falls back to settings if None.
        """
        from backend.core.config import get_settings
        settings = get_settings()

        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self._client = httpx.AsyncClient(timeout=15.0)

    # ── Public API ────────────────────────────────────────────

    async def send_alert(
        self,
        alert: Dict[str, Any],
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a single formatted alert to Telegram.

        Args:
            alert:   Alert dict with keys: category, severity, title, message,
                     project_name (optional), days_remaining (optional).
            chat_id: Override the default chat ID.

        Returns:
            Dict with ``success`` bool and ``message_id`` or ``error``.
        """
        target_chat = chat_id or self.chat_id

        if not self.bot_token or not target_chat:
            logger.warning("[Agent D] Telegram credentials missing – skipping send")
            return {"success": False, "error": "Telegram credentials not configured"}

        text = self._format_alert(alert)

        try:
            url = self.SEND_MESSAGE_URL.format(token=self.bot_token)
            resp = await self._client.post(url, json={
                "chat_id": target_chat,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
            data = resp.json()

            if resp.status_code == 200 and data.get("ok"):
                msg_id = data["result"]["message_id"]
                logger.info(f"[Agent D] Telegram message sent (id={msg_id})")
                return {"success": True, "message_id": msg_id}

            error_desc = data.get("description", "Unknown error")
            logger.error(f"[Agent D] Telegram API error: {error_desc}")
            return {"success": False, "error": error_desc}

        except Exception as exc:
            logger.error(f"[Agent D] Telegram send failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def send_alerts_batch(
        self,
        alerts: List[Dict[str, Any]],
        project_name: str = "",
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a summary message containing multiple alerts in one go.

        Args:
            alerts:       List of alert dicts.
            project_name: Project name for the header.
            chat_id:      Override chat ID.

        Returns:
            Dict with ``success``, ``message_id``, and ``alerts_count``.
        """
        target_chat = chat_id or self.chat_id

        if not self.bot_token or not target_chat:
            logger.warning("[Agent D] Telegram credentials missing – skipping batch")
            return {"success": False, "error": "Telegram credentials not configured"}

        text = self._format_batch(alerts, project_name)

        try:
            url = self.SEND_MESSAGE_URL.format(token=self.bot_token)
            resp = await self._client.post(url, json={
                "chat_id": target_chat,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
            data = resp.json()

            if resp.status_code == 200 and data.get("ok"):
                msg_id = data["result"]["message_id"]
                logger.info(
                    f"[Agent D] Telegram batch sent ({len(alerts)} alerts, id={msg_id})"
                )
                return {
                    "success": True,
                    "message_id": msg_id,
                    "alerts_count": len(alerts),
                }

            error_desc = data.get("description", "Unknown error")
            logger.error(f"[Agent D] Telegram batch error: {error_desc}")
            return {"success": False, "error": error_desc}

        except Exception as exc:
            logger.error(f"[Agent D] Telegram batch failed: {exc}")
            return {"success": False, "error": str(exc)}

    async def close(self):
        """Close underlying HTTP client."""
        await self._client.aclose()

    # ── Formatting helpers ────────────────────────────────────

    def _format_alert(self, alert: Dict[str, Any]) -> str:
        """Render a single alert into Telegram Markdown."""
        cat = alert.get("category", "general")
        emoji = CATEGORY_EMOJI.get(cat, "🔔")
        severity = alert.get("severity", "medium")
        sev_label = SEVERITY_LABEL.get(severity, "🟡 MEDIUM")

        title = alert.get("title", "Alert")
        message = alert.get("message", "")
        project = alert.get("project_name", "")
        days = alert.get("days_remaining")

        lines = [
            f"{emoji} *{title}*",
            f"Severity: {sev_label}",
        ]
        if project:
            lines.append(f"Project: _{project}_")
        if days is not None:
            lines.append(f"⏰ *{days} day(s) remaining*")
        if message:
            lines.append(f"\n{message}")

        lines.append(f"\n🕐 {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}")
        return "\n".join(lines)

    def _format_batch(self, alerts: List[Dict[str, Any]], project_name: str) -> str:
        """Render multiple alerts into a single summary message."""
        header = f"🏗️ *Buildora Alert Summary*"
        if project_name:
            header += f"\nProject: _{project_name}_"
        header += f"\n{'─' * 28}\n"

        items = []
        for i, alert in enumerate(alerts, 1):
            cat = alert.get("category", "general")
            emoji = CATEGORY_EMOJI.get(cat, "🔔")
            severity = alert.get("severity", "medium")
            sev_label = SEVERITY_LABEL.get(severity, "🟡")
            title = alert.get("title", "Alert")
            days = alert.get("days_remaining")

            line = f"{i}. {emoji} *{title}*  [{sev_label}]"
            if days is not None:
                line += f"  — {days}d left"
            items.append(line)

        footer = f"\n{'─' * 28}\n🕐 {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}"
        return header + "\n".join(items) + footer
