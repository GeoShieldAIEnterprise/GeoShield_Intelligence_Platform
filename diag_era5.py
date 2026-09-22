import sys
sys.path.insert(0, ".")

from core.engines.main_engine import main_engine

connector = main_engine.connectors.get("ERA5-OpenMeteo")

if connector is None:
    print("Connector 'ERA5-OpenMeteo' is not registered in main_engine.connectors at all.")
else:
    print(f"Connector found: {connector}")
    print(f"is_enabled(): {connector.is_enabled()}")

    result = connector.search()
    print(f"success: {result.success}")
    print(f"error: {result.error}")
    print(f"data (first 500 chars): {str(result.data)[:500]}")
