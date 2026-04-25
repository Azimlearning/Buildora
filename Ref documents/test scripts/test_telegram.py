"""
Quick Telegram Alert Tester
============================
Run:  ./venv/bin/python test_telegram.py

Edit the alert below to test different scenarios.
"""

import asyncio
from backend.agents.agent_d.telegram_notifier import TelegramNotifier


# ── Change these to test different alerts ─────────────────────────

ALERTS = [
    {
        "category": "delay_detected",       # doc_submission | payment_due | account_receivable | extension_of_time | delay_detected | cost_overrun | permit_renewal | general
        "severity": "critical",             # critical | high | medium | low | info
        "title": "🚧 New Delay: Pile Driving Behind Schedule",
        "message": "Pile driving for Block C is 4 days behind. Subcontractor cited machinery breakdown. Escalation recommended.",
        "project_name": "Residensi Harmoni KL",
        "days_remaining": 0,
    },
    {
        "category": "cost_overrun",
        "severity": "high",
        "title": "Steel Price Surge — Budget Impact",
        "message": "Steel rebar cost increased 12% from RM 2,800/ton to RM 3,136/ton. Total project impact: +RM 87,000 (9.2% variance).",
        "project_name": "Residensi Harmoni KL",
        "days_remaining": None,
    },
    {
        "category": "payment_due",
        "severity": "critical",
        "title": "Subcon Payment Overdue",
        "message": "ABC Construction Sdn Bhd — Progress Claim #6 (RM 62,000) overdue by 2 days. Risk of work stoppage.",
        "project_name": "Residensi Harmoni KL",
        "days_remaining": -2,
    },
]


async def main():
    notifier = TelegramNotifier()

    print("=" * 50)
    print("🏗️  Buildora Telegram Alert Tester")
    print("=" * 50)

    # ── Send individually ──
    # for alert in ALERTS:
    #     result = await notifier.send_alert(alert)
    #     status = "✅ Sent" if result["success"] else f"❌ Failed: {result['error']}"
    #     print(f"  {status} — {alert['title']}")

    # ── Send as batch summary ──
    result = await notifier.send_alerts_batch(
        alerts=ALERTS,
        project_name="Residensi Harmoni KL",
    )

    if result.get("success"):
        print(f"\n✅ Batch sent! ({result['alerts_count']} alerts)")
        print(f"   Message ID: {result['message_id']}")
    else:
        print(f"\n❌ Failed: {result['error']}")

    await notifier.close()
    print("\nDone! Check your Telegram 📱")


if __name__ == "__main__":
    asyncio.run(main())
