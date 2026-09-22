# -*- coding: utf-8 -*-
import io

path = r"frontend\templates\index.html"
with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

SIREN = "\U0001F6A8"

old_body = (
    '            <div class="drought-summary-panel">\n'
    '                <div class="drought-summary-card">\n'
    "                    <span>Total alerts</span>\n"
    '                    <strong id="alertsTotalCount">--</strong>\n'
    "                </div>\n"
    "            </div>\n"
    '            <div id="alertsList" style="padding:16px; overflow-y:auto; max-height:70vh;">\n'
    "                Loading alerts...\n"
    "            </div>\n"
    "        </section>"
)

new_body = (
    '            <div class="analytics-cards-grid">\n'
    '                <div class="analytics-card" id="alertsActiveCard">\n'
    "                    <h3>Active Alerts</h3>\n"
    '                    <div id="alertsActiveSummary" class="analytics-card-body">Loading...</div>\n'
    "                </div>\n"
    '                <div class="analytics-card" id="alertsHistoricalCard">\n'
    "                    <h3>Historical Alerts</h3>\n"
    '                    <div id="alertsHistoricalSummary" class="analytics-card-body">Loading...</div>\n'
    "                </div>\n"
    "            </div>\n"
    "        </section>"
)

count = content.count(old_body)
if count != 1:
    print("[FAIL] index.html: expected exactly 1 match for old Alerts page body, found %d" % count)
else:
    content = content.replace(old_body, new_body, 1)
    print("[OK] index.html: replaced Alerts page body with cards grid")

# Insert the Alerts modal right after the Analytics modal block.
anchor = '<script src="/static/agricultureengine.js"></script>'
alerts_modal = (
    '<div id="alertsModalBackdrop" class="analytics-modal-backdrop">\n'
    '    <div class="analytics-modal">\n'
    '        <div class="analytics-modal-header">\n'
    '            <h3 id="alertsModalTitle">Details</h3>\n'
    '            <div style="display:flex; gap:10px; align-items:center;">\n'
    '                <button type="button" id="alertsClearHistoryBtn" class="analytics-modal-close" style="display:none;">Clear All Historical Alerts</button>\n'
    '                <button type="button" id="alertsModalCloseBtn" class="analytics-modal-close">&#8592; Back to Alerts</button>\n'
    "            </div>\n"
    "        </div>\n"
    '        <div id="alertsModalBody" class="analytics-modal-body">Loading...</div>\n'
    "    </div>\n"
    "</div>\n\n"
)

anchor_count = content.count(anchor)
if anchor_count != 1:
    print("[FAIL] index.html: expected exactly 1 match for agricultureengine.js anchor, found %d" % anchor_count)
else:
    content = content.replace(anchor, alerts_modal + anchor, 1)
    print("[OK] index.html: inserted alertsModalBackdrop")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(content)
