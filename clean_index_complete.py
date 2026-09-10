from pathlib import Path

html_path = Path("frontend/templates/index.html")
text = html_path.read_text(encoding="utf-8")

# Completely clean the header and card titles of any broken multi-byte sequences
# Replace the live map title container text directly
import re
text = re.sub(r'<div[^>]*id="liveMapTitle"[^>]*>.*?</div>', '<div id="liveMapTitle" class="workspace-title">&#128640; Live Map -- Sentinel-2 Imagery</div>', text, flags=re.DOTALL)

# Clean up sidebar menu items
text = text.replace("ðŸ“Š Dashboard", "&#128202; Dashboard")
text = text.replace("ðŸš€ Live Map", "&#128640; Live Map")
text = text.replace("ðŸ“ˆ Analytics", "&#128200; Analytics")
text = text.replace("ðŸ”” Alerts", "&#128276; Alerts")
text = text.replace("ðŸ“ Reports", "&#128196; Reports")
text = text.replace("ðŸCEŠ Flood Engine", "&#127754; Flood Engine")
text = text.replace("ðŸ“¥ Fire Engine", "&#128293; Fire Engine")
text = text.replace("ðŸCE Earthquake Engine", "&#127757; Earthquake Engine")
text = text.replace("ðŸCE¾ Agriculture", "&#127806; Agriculture")

html_path.write_text(text, encoding="utf-8")
print("Cleaned index.html successfully.")
