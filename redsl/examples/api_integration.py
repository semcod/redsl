from __future__ import annotations

from typing import Any

from ._common import load_example_yaml, parse_scenario, print_banner


def run_api_integration_example(scenario: str = "default", source: str | None = None) -> dict[str, Any]:
    data = load_example_yaml("api_integration", scenario=scenario, source=source)
    base_url = data.get("base_url", "http://localhost:8000")

    print_banner(data.get("title", "ReDSL API — przykłady curl"))

    for section in data.get("curl_examples", []):
        print(section.get("heading", ""))
        template = section.get("template", "")
        print(template.format(base=base_url))

    print_banner(data.get("python_client_title", "ReDSL API — klient Python (httpx)"))
    print(data.get("python_client", ""))

    print_banner(data.get("websocket_title", "ReDSL API — WebSocket (real-time)"))
    print(data.get("websocket_client", ""))

    footer = data.get("footer", {})
    print("\n" + "=" * 60)
    print(f"  {footer.get('title', 'Uruchom serwer:')}")
    print(f"    {footer.get('server_command', 'uvicorn app.api:app --port 8000')}")
    print("  Potem użyj powyższych komend.")
    print("=" * 60)

    return {"scenario": data, "base_url": base_url}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    scenario = parse_scenario(argv)
    return run_api_integration_example(scenario=scenario)


if __name__ == "__main__":
    main()
