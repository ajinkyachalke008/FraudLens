import logging
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

def generate_pdf_report(case_id: str, narrative_text: str, metadata: dict) -> bytes:
    """
    Generates a branded PDF dossier for the Pune Police Cybercrime Cell.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=20,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=30,
        alignment=1 # Center
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=12
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=15,
        spaceAfter=10
    )

    elements = []
    
    # Header Branding
    elements.append(Paragraph("<b>PUNE POLICE CYBERCRIME CELL</b>", title_style))
    elements.append(Paragraph("FRAUDLENS AUTOMATED INTELLIGENCE DOSSIER", subtitle_style))
    
    # Meta Info
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    meta_text = f"<b>Case ID:</b> {case_id}<br/><b>Generated:</b> {date_str}<br/><b>Risk Assessment:</b> {metadata.get('risk_level', 'HIGH')}"
    elements.append(Paragraph(meta_text, body_style))
    elements.append(Spacer(1, 20))
    
    # Narrative Injection
    # We expect the LLM to provide paragraphs separated by double newlines.
    # If the LLM generates a numbered list or header, we do simple formatting.
    for block in narrative_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
            
        # Detect fake headers (short lines without punctuation)
        if len(block) < 50 and not block.endswith("."):
            elements.append(Paragraph(f"<b>{block}</b>", header_style))
        else:
            # Handle bullet points
            if block.startswith("- "):
                bullets = block.split("\n")
                for bullet in bullets:
                    elements.append(Paragraph(bullet, body_style))
            else:
                elements.append(Paragraph(block, body_style))
    
    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<i>CONFIDENTIAL - FOR OFFICIAL LAW ENFORCEMENT USE ONLY</i>", subtitle_style))
    
    try:
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return b""
