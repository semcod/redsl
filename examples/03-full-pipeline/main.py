#!/usr/bin/env python3
"""
ReDSL — Przykład 03: Pełny pipeline refaktoryzacji

Pokazuje kompletny cykl:
    PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER

⚠️  Wymaga OPENAI_API_KEY (lub innego providera LLM)

Uruchomienie:
    export OPENAI_API_KEY=sk-...
    python main.py

    # Z lokalnym modelem (Ollama):
    python main.py --model ollama/llama3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import AgentConfig
from app.orchestrator import RefactorOrchestrator


# ──────────────────────────────────────────────────────────
# Przykładowy kod do refaktoryzacji
# ──────────────────────────────────────────────────────────

SAMPLE_CODE = '''
def process_order(order, user, db, mailer, logger, inventory, pricing, tax, discount, shipping):
    """Funkcja z CC=25 i fan-out=10 — idealny kandydat do refaktoryzacji."""
    if not order:
        logger.error("No order")
        return None
    if not user:
        logger.error("No user")
        return None
    if order.status == "cancelled":
        logger.info("Order cancelled")
        return None
    if order.status == "completed":
        logger.info("Order already completed")
        return order

    items = order.items
    total = 0
    for item in items:
        if item.type == "physical":
            stock = inventory.check(item.sku)
            if stock <= 0:
                logger.warning(f"Out of stock: {item.sku}")
                if item.backorder_allowed:
                    inventory.backorder(item.sku, item.quantity)
                else:
                    return {"error": f"Out of stock: {item.sku}"}
            price = pricing.get_price(item.sku)
            if discount.is_eligible(user, item):
                price = discount.apply(price, user.tier)
            tax_amount = tax.calculate(price, user.region)
            total += price + tax_amount
        elif item.type == "digital":
            price = pricing.get_price(item.sku)
            total += price
        elif item.type == "subscription":
            price = pricing.get_subscription_price(item.sku, item.period)
            total += price
        else:
            logger.warning(f"Unknown item type: {item.type}")

    if total > 0:
        shipping_cost = shipping.calculate(order.address, items)
        total += shipping_cost
        order.total = total
        order.status = "processing"
        db.save(order)
        mailer.send_confirmation(user.email, order)
        logger.info(f"Order {order.id} processed: ${total}")
        return order
    else:
        logger.error("Empty order total")
        return None
'''

SAMPLE_TOON = """
ALERTS[2]:
  !!! cc_exceeded      process_order = 25 (limit:15)
  !!! high_fan_out     process_order = 10 (limit:10)

MODULES[1]:
  M[orders/service.py] 55L C:0 F:1 CC↑25 D:0 (python)
"""


def main():
    model = "gpt-4o-mini"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    # ──────────────────────────────────────────────────────
    # Konfiguracja
    # ──────────────────────────────────────────────────────
    config = AgentConfig.from_env()
    config.llm.model = model
    config.refactor.dry_run = True          # Nie aplikuj zmian
    config.refactor.reflection_rounds = 1   # Jedna runda refleksji

    orchestrator = RefactorOrchestrator(config)

    print("=" * 60)
    print(f"  ReDSL — Pełny pipeline")
    print(f"  Model: {model}")
    print("=" * 60)

    # ──────────────────────────────────────────────────────
    # Uruchom cykl
    # ──────────────────────────────────────────────────────
    report = orchestrator.run_from_toon_content(
        project_toon=SAMPLE_TOON,
        source_files={"orders/service.py": SAMPLE_CODE},
        max_actions=3,
    )

    # ──────────────────────────────────────────────────────
    # Raport
    # ──────────────────────────────────────────────────────
    print(f"\n  Cykl #{report.cycle_number}")
    print(f"  Analiza:       {report.analysis_summary}")
    print(f"  Decyzje:       {report.decisions_count}")
    print(f"  Propozycje:    {report.proposals_generated}")
    print(f"  Zaaplikowane:  {report.proposals_applied}")
    print(f"  Odrzucone:     {report.proposals_rejected}")

    if report.errors:
        print(f"\n  Błędy:")
        for err in report.errors:
            print(f"    - {err}")

    # Wyniki w refactor_output/
    print(f"\n  Propozycje zapisane w: {config.refactor.output_dir}")

    # ──────────────────────────────────────────────────────
    # Pamięć
    # ──────────────────────────────────────────────────────
    stats = orchestrator.get_memory_stats()
    print(f"\n  Pamięć agenta: {stats['memory']}")
    print(f"  Wywołania LLM: {stats['total_llm_calls']}")


if __name__ == "__main__":
    main()
