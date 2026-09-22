import io
import json
import subprocess
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from core.engines.main_engine import main_engine
from backend.analytics.analytics_engine import analytics_engine
from core.config import settings

router = APIRouter()

HAZARDS = ["fire", "agriculture", "drought", "flood"]

SEVERITY_COLORS = {
    "Low": colors.HexColor("#2e7d32"),
    "Moderate": colors.HexColor("#f9a825"),
    "High": colors.HexColor("#ef6c00"),
    "Extreme": colors.HexColor("#c62828"),
}

GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SECTION_MARKERS = ["EXECUTIVE_SUMMARY", "FIRE", "AGRICULTURE", "DROUGHT", "FLOOD", "RECOMMENDATIONS"]


def _parse_sections(raw_text: str) -> dict:
    sections = {}
    current_key = None
    current_lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        matched = None
        for marker in SECTION_MARKERS:
            if stripped.upper().startswith(f"## {marker}") or stripped.upper() == marker:
                matched = marker
                break
        if matched:
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = matched
            current_lines = []
        elif current_key:
            current_lines.append(line)
    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()
    return sections


def _local_fallback_sections(county: str, hazard_data: dict, overall_risk: str) -> dict:
    sections = {
        "EXECUTIVE_SUMMARY": (
            f"This report presents the current GeoShield AI disaster-intelligence assessment "
            f"for {county} County, Kenya. The overall average risk across the four monitored "
            f"hazard categories - Agriculture, Fire, Flood, and Drought - is currently assessed "
            f"as {overall_risk}. This assessment is derived from GeoShield AI's Analytics Engine, "
            f"which aggregates hazard-specific severity scores drawn from satellite, weather, "
            f"and geospatial data sources monitoring the county. Officials and response "
            f"coordinators should treat this report as a current snapshot of monitored "
            f"conditions rather than a substitute for on-the-ground verification."
        )
    }
    for hazard in HAZARDS:
        level = hazard_data.get(hazard, {}).get("risk_level", "--")
        sources = ", ".join(hazard_data.get(hazard, {}).get("satellites", []))
        sections[hazard.upper()] = (
            f"The {hazard} risk level for {county} is currently assessed as {level}. "
            f"This assessment draws on monitoring inputs from {sources or 'available GeoShield AI sources'}. "
            f"Continued monitoring is recommended to track any change in this status."
        )
    sections["RECOMMENDATIONS"] = (
        "- Maintain routine monitoring of all four hazard categories for this county.\n"
        "- Escalate response planning if any individual hazard moves to High or Extreme.\n"
        "- Cross-check GeoShield AI's assessment against local field reports where available.\n"
        "- Review this report alongside the corresponding county dashboard for the most current status."
    )
    return sections


def _call_gemini_via_curl(prompt: str) -> str | None:
    if not settings.reports_gemini_api_key:
        return None

    url = f"{GEMINI_URL}?key={settings.reports_gemini_api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]})

    try:
        result = subprocess.run(
            [
                "curl.exe", "-s", "-X", "POST", url,
                "-H", "Content-Type: application/json",
                "--data-binary", "@-",
            ],
            input=payload.encode("utf-8"),
            capture_output=True,
            timeout=settings.http_timeout,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout.decode("utf-8"))
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        ).strip()
        return text or None
    except Exception:
        return None


def _generate_report_sections(county: str, hazard_data: dict, overall_risk: str) -> dict:
    hazard_lines = "\n".join(
        f"- {hazard.capitalize()}: {hazard_data.get(hazard, {}).get('risk_level', '--')} "
        f"(monitored via {', '.join(hazard_data.get(hazard, {}).get('satellites', []))})"
        for hazard in HAZARDS
    )

    prompt = (
        f"Write a formal disaster-intelligence briefing for officials regarding {county} County, "
        f"Kenya, for GeoShield AI Enterprise. Base it ONLY on the data below - do not invent "
        f"numbers, incidents, or details not listed here. If a hazard is 'Low', do not describe "
        f"an emergency; describe routine monitored status instead.\n\n"
        f"Overall Average Risk: {overall_risk}\n"
        f"{hazard_lines}\n\n"
        "Structure your response using EXACTLY these section markers, each on its own line, "
        "in this order, with plain-text paragraphs (no markdown, no bullet symbols except in "
        "RECOMMENDATIONS):\n\n"
        "## EXECUTIVE_SUMMARY\n"
        "(3-4 sentences: overview of the county's overall risk posture and what it means "
        "for officials reading this report)\n\n"
        "## FIRE\n"
        "(2-3 sentences on fire risk status, referencing its specific level)\n\n"
        "## AGRICULTURE\n"
        "(2-3 sentences on agricultural risk status, referencing its specific level)\n\n"
        "## DROUGHT\n"
        "(2-3 sentences on drought risk status, referencing its specific level)\n\n"
        "## FLOOD\n"
        "(2-3 sentences on flood risk status, referencing its specific level)\n\n"
        "## RECOMMENDATIONS\n"
        "(3-5 short bullet points, each starting with '- ', giving practical next steps "
        "appropriate to the severity levels shown - routine monitoring for Low, closer "
        "attention for Moderate, active response planning for High/Extreme)\n"
    )

    text = _call_gemini_via_curl(prompt)
    if text:
        parsed = _parse_sections(text)
        if len(parsed) >= 4:
            return parsed

    return _local_fallback_sections(county, hazard_data, overall_risk)


def _build_pdf(county: str) -> bytes:
    hazard_data = {}
    for hazard in HAZARDS:
        try:
            hazard_data[hazard] = main_engine.get_hazard_summary(hazard, county=county)
        except Exception as exc:
            hazard_data[hazard] = {"risk_level": "--", "error": str(exc)}

    overall_risk = "--"
    try:
        county_analytics = analytics_engine.get_county_analytics(county=county)
        counties = county_analytics.get("counties", [])
        if counties:
            overall_risk = counties[0].get("overall_risk") or "--"
    except Exception:
        pass

    sections = _generate_report_sections(county, hazard_data, overall_risk)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "GeoShieldTitle", parent=styles["Title"], textColor=colors.HexColor("#1a237e")
    )
    section_heading_style = ParagraphStyle(
        "GeoShieldSectionHeading", parent=styles["Heading3"],
        textColor=colors.HexColor("#1a237e"), spaceBefore=10, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "GeoShieldBody", parent=styles["Normal"], leading=15, spaceAfter=6,
    )
    footnote_style = ParagraphStyle(
        "GeoShieldFootnote", parent=styles["Normal"], fontSize=8,
        textColor=colors.grey, leading=11,
    )

    elements = [
        Paragraph("GeoShield AI Enterprise", title_style),
        Paragraph(f"Disaster Intelligence Report &mdash; {county} County", styles["Heading2"]),
        Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
        Paragraph(f"<b>Overall Average Risk:</b> {overall_risk}", styles["Heading3"]),
        Spacer(1, 0.3 * cm),
        HRFlowable(width="100%", color=colors.HexColor("#1a237e"), thickness=1),
        Spacer(1, 0.3 * cm),
    ]

    elements.append(Paragraph("Executive Summary", section_heading_style))
    elements.append(Paragraph(sections.get("EXECUTIVE_SUMMARY", "").replace("\n", " "), body_style))

    elements.append(Paragraph("Hazard-by-Hazard Assessment", section_heading_style))
    for hazard in HAZARDS:
        level = hazard_data[hazard].get("risk_level", "--")
        elements.append(
            Paragraph(f"<b>{hazard.capitalize()}</b> &mdash; {level}", styles["Heading4"])
        )
        elements.append(
            Paragraph(sections.get(hazard.upper(), "").replace("\n", " "), body_style)
        )

    table_data = [["Hazard", "Risk Level"]]
    row_colors = []
    for hazard in HAZARDS:
        level = hazard_data[hazard].get("risk_level", "--")
        table_data.append([hazard.capitalize(), level])
        row_colors.append(SEVERITY_COLORS.get(level, colors.black))

    table = Table(table_data, colWidths=[8 * cm, 6 * cm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, c in enumerate(row_colors, start=1):
        style_cmds.append(("TEXTCOLOR", (1, i), (1, i), c))
        style_cmds.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
    table.setStyle(TableStyle(style_cmds))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(table)
    elements.append(Spacer(1, 0.4 * cm))

    elements.append(Paragraph("Recommendations", section_heading_style))
    for line in sections.get("RECOMMENDATIONS", "").splitlines():
        line = line.strip()
        if line:
            elements.append(Paragraph(line, body_style))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Data Sources &amp; Methodology", section_heading_style))
    for hazard in HAZARDS:
        sources = ", ".join(hazard_data[hazard].get("satellites", [])) or "N/A"
        elements.append(
            Paragraph(f"<b>{hazard.capitalize()}:</b> {sources}", footnote_style)
        )
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "This report reflects GeoShield AI's current hazard monitoring status for the "
        "selected county, aggregated by the Analytics Engine from the hazard-specific "
        "engines listed above. Where a hazard's assessment is derived from forecast, "
        "anticipatory, or static reference data rather than a live real-time measurement, "
        "this should not be interpreted as confirmed active conditions on the ground. "
        "This report is intended to support, not replace, on-the-ground verification and "
        "official situational assessment.",
        footnote_style,
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/reports/pdf")
def generate_pdf_report(county: str):
    if not county:
        raise HTTPException(status_code=400, detail="county is required")
    pdf_bytes = _build_pdf(county)
    filename = f"GeoShield_Report_{county.replace(' ', '_')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
