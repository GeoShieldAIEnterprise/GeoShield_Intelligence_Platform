path = r"core\connectors\sentinel2\sentinel2_ndvi_connector.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """                if sample_count and mean is not None:
                    return round(float(mean), 4)

            return None

        except (ValueError, KeyError, TypeError):
            return None"""

new = """                if sample_count and mean is not None:
                    return round(float(mean), 4)

            import logging
            logging.getLogger(__name__).warning(
                "NDVI no valid interval found. Raw response body: %s", text[:500]
            )
            return None

        except (ValueError, KeyError, TypeError) as exc:
            import logging
            logging.getLogger(__name__).warning(
                "NDVI parse failed (%s). Raw response body: %s", exc, text[:500]
            )
            return None"""

if old not in content:
    print("Pattern not found -- file may differ from expected. No changes made.")
else:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new, 1))
    print("Added deeper error logging.")
