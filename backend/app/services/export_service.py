import io
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

from app.services.session_service import load_session_history

logger = logging.getLogger("rag_backend.services.export_service")

def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safe for filenames."""
    if not name:
        return "research_session"
    clean = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
    return clean.strip("_")[:60] or "research_session"

def export_as_json(session_data: Dict[str, Any]) -> str:
    """
    Exports research session data to a formatted JSON string.

    Args:
        session_data (Dict[str, Any]): Session payload.

    Returns:
        str: Pretty-printed JSON string.
    """
    return json.dumps(session_data, indent=2, ensure_ascii=False)

def export_as_markdown(session_data: Dict[str, Any]) -> str:
    """
    Exports research session data into a structured Markdown document.

    Args:
        session_data (Dict[str, Any]): Session payload.

    Returns:
        str: Markdown document string.
    """
    title = session_data.get("title", "Research Session")
    session_id = session_data.get("session_id") or session_data.get("session_uuid", "N/A")
    created_at = session_data.get("created_at", "N/A")
    messages = session_data.get("messages", [])

    lines = [
        f"# AI Research Workspace Transcript",
        f"**Session Title**: {title}",
        f"**Session ID**: `{session_id}`",
        f"**Export Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Total Conversation Turns**: {len(messages)}",
        f"---",
        ""
    ]

    for idx, msg in enumerate(messages, start=1):
        role = msg.get("role", "assistant").capitalize()
        user_question = msg.get("user_question") or ""
        assistant_answer = msg.get("assistant_answer") or msg.get("content") or ""
        latency = msg.get("latency", 0.0)
        logs = msg.get("retrieval_logs", [])

        lines.append(f"## Turn {idx}: {role}")
        if user_question:
            lines.append(f"### User Question")
            lines.append(f"> {user_question}")
            lines.append("")

        if assistant_answer:
            lines.append(f"### Grounded AI Response")
            lines.append(assistant_answer)
            lines.append("")

        if latency:
            lines.append(f"_Processing Latency_: `{latency}s`")
            lines.append("")

        if logs:
            lines.append("### Source Attribution & Relevance Scores")
            lines.append("| Rank | Document UUID | Chunk UUID | Page | Semantic | BM25 | RRF | Cross-Encoder | Strategy |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for log in logs:
                r = log.get("retrieval_rank", 1)
                doc = str(log.get("document_uuid", "N/A"))[:12]
                chunk = str(log.get("chunk_uuid", "N/A"))[:16]
                page = log.get("page_number", 1)
                sem = log.get("semantic_score", 0.0)
                bm = log.get("bm25_score", 0.0)
                rrf = log.get("rrf_score", 0.0)
                cross = log.get("reranker_score", 0.0)
                strat = log.get("retrieval_strategy", "Hybrid RRF")
                lines.append(f"| {r} | `{doc}` | `{chunk}` | p. {page} | {sem:.3f} | {bm:.2f} | {rrf:.4f} | {cross:.3f} | {strat} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)

def export_as_pdf(session_data: Dict[str, Any]) -> bytes:
    """
    Exports research session data into a downloadable PDF document using ReportLab.

    Args:
        session_data (Dict[str, Any]): Session payload.

    Returns:
        bytes: Binary PDF file bytes.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e293b")
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#64748b")
        )
        heading_style = ParagraphStyle(
            "TurnHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f172a")
        )
        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )

        story = []

        title_text = session_data.get("title", "Research Session")
        session_id = session_data.get("session_id") or session_data.get("session_uuid", "N/A")
        messages = session_data.get("messages", [])

        story.append(Paragraph(f"AI Research Workspace Transcript: {title_text}", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Session ID: {session_id} | Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        for idx, msg in enumerate(messages, start=1):
            q_text = msg.get("user_question") or ""
            a_text = msg.get("assistant_answer") or msg.get("content") or ""
            logs = msg.get("retrieval_logs", [])

            story.append(Paragraph(f"Turn {idx}: Research Query & Answer", heading_style))
            story.append(Spacer(1, 4))

            if q_text:
                story.append(Paragraph(f"<b>User Question:</b> {q_text}", body_style))
                story.append(Spacer(1, 4))

            if a_text:
                # Basic HTML clean formatting for ReportLab Paragraph
                clean_answer = a_text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                story.append(Paragraph(f"<b>Grounded AI Response:</b><br/>{clean_answer}", body_style))
                story.append(Spacer(1, 6))

            if logs:
                story.append(Paragraph("<b>Source Attribution & Relevance Scores:</b>", body_style))
                story.append(Spacer(1, 4))

                table_data = [["Rank", "Document UUID", "Page", "Semantic", "BM25", "RRF", "Cross-Enc", "Strategy"]]
                for log in logs:
                    table_data.append([
                        str(log.get("retrieval_rank", 1)),
                        str(log.get("document_uuid", "N/A"))[:10],
                        f"p. {log.get('page_number', 1)}",
                        f"{log.get('semantic_score', 0.0):.3f}",
                        f"{log.get('bm25_score', 0.0):.2f}",
                        f"{log.get('rrf_score', 0.0):.4f}",
                        f"{log.get('reranker_score', 0.0):.3f}",
                        str(log.get("retrieval_strategy", "Hybrid RRF"))
                    ])

                t = Table(table_data, colWidths=[35, 90, 40, 50, 45, 50, 60, 75])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))

            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
    except Exception as e:
        logger.exception(f"ReportLab PDF generation error: {e}")
        # Fallback to plain text bytes format if ReportLab raises error
        md_text = export_as_markdown(session_data)
        return md_text.encode("utf-8")

def export_session_content(session_id_or_uuid: str, export_format: str = "markdown") -> Tuple[Any, str, str]:
    """
    Retrieves and exports a research session transcript in the requested format.

    Args:
        session_id_or_uuid (str): Session UUID or integer ID.
        export_format (str): 'markdown', 'json', or 'pdf'.

    Returns:
        Tuple[Any, str, str]: (content_payload, mime_type, filename)

    Raises:
        ValueError: If session not found.
    """
    session_data = load_session_history(session_id_or_uuid)
    safe_title = sanitize_filename(session_data.get("title", "research_session"))
    fmt = str(export_format).lower().strip()

    if fmt in ("json", "application/json"):
        content = export_as_json(session_data)
        mime_type = "application/json"
        filename = f"{safe_title}.json"
    elif fmt in ("pdf", "application/pdf"):
        content = export_as_pdf(session_data)
        mime_type = "application/pdf"
        filename = f"{safe_title}.pdf"
    else:
        content = export_as_markdown(session_data)
        mime_type = "text/markdown"
        filename = f"{safe_title}.md"

    logger.info(f"Exported session '{session_id_or_uuid}' as format='{fmt}' -> filename='{filename}'")
    return content, mime_type, filename
