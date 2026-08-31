import io
import html
import datetime
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    HTML = None
    WEASYPRINT_AVAILABLE = False

class PDFGeneratorService:
    """
    Generates beautiful, production-grade PDF plagiarism analysis reports using WeasyPrint.
    Uses HTML templates and CSS Paged Media rules.
    """

    @staticmethod
    def _get_highlighted_html(text: str, sentences: list[dict], matches: list[dict]) -> str:
        """
        Reconstructs the original document text with word-level <mark> highlights
        based on plagiarism coordinate mappings.
        """
        # Map sentence start_char to its match for quick lookup
        matches_map = {m["query_sentence"]["start_char"]: m for m in matches}
        
        html_parts = []
        last_offset = 0
        
        for s in sentences:
            start = s["start_char"]
            end = s["end_char"]
            
            # Append any raw text between sentences (spaces, newlines, etc.)
            if start > last_offset:
                raw_between = text[last_offset:start]
                # Replace newlines with <br> to preserve line breaks
                html_parts.append(html.escape(raw_between).replace("\n", "<br>"))
                
            sent_text = s["text"]
            match = matches_map.get(start)
            
            if match:
                highlights = match.get("highlights", [])
                if highlights:
                    # Sort highlights by relative start offset in the sentence
                    sorted_hls = []
                    for hl in highlights:
                        rel_start = hl["start_char"] - start
                        rel_end = hl["end_char"] - start
                        # Make sure boundaries are within bounds
                        if 0 <= rel_start < rel_end <= len(sent_text):
                            sorted_hls.append((rel_start, rel_end, hl["text"]))
                            
                    sorted_hls.sort(key=lambda x: x[0])
                    
                    # Merge overlapping or touching highlights relative to sentence
                    merged_hls = []
                    if sorted_hls:
                        merged_hls.append(sorted_hls[0])
                        for curr in sorted_hls[1:]:
                            prev = merged_hls[-1]
                            if curr[0] <= prev[1]:
                                merged_hls[-1] = (prev[0], max(prev[1], curr[1]), sent_text[prev[0]:max(prev[1], curr[1])])
                            else:
                                merged_hls.append(curr)
                                
                    sent_html = []
                    last_sent_idx = 0
                    
                    for rel_start, rel_end, hl_text in merged_hls:
                        if rel_start > last_sent_idx:
                            sent_html.append(html.escape(sent_text[last_sent_idx:rel_start]))
                        
                        if match["match_type"] == "lexical":
                            mark_class = "mark-lexical"
                        elif match["match_type"] == "hybrid":
                            mark_class = "mark-hybrid"
                        else:
                            mark_class = "mark-semantic"
                        sent_html.append(f'<mark class="{mark_class}">{html.escape(sent_text[rel_start:rel_end])}</mark>')
                        last_sent_idx = rel_end
                        
                    if last_sent_idx < len(sent_text):
                        sent_html.append(html.escape(sent_text[last_sent_idx:]))
                    
                    sentence_html_content = "".join(sent_html)
                else:
                    if match["match_type"] == "lexical":
                        mark_class = "mark-lexical"
                    elif match["match_type"] == "hybrid":
                        mark_class = "mark-hybrid"
                    else:
                        mark_class = "mark-semantic"
                    sentence_html_content = f'<mark class="{mark_class}">{html.escape(sent_text)}</mark>'
            else:
                sentence_html_content = html.escape(sent_text)
                
            html_parts.append(sentence_html_content)
            last_offset = end
            
        # Append remaining trailing text
        if last_offset < len(text):
            raw_tail = text[last_offset:]
            html_parts.append(html.escape(raw_tail).replace("\n", "<br>"))
            
        return "".join(html_parts)

    @classmethod
    def generate_report(cls, data: dict) -> bytes:
        """
        Builds the HTML report structure and compiles it to PDF.
        """
        filename = data.get("filename", "unknown_document.txt")
        text = data.get("text", "")
        char_count = data.get("char_count", 0)
        sentence_count = data.get("sentence_count", 0)
        sentences = data.get("sentences", [])
        
        analysis = data.get("analysis", {}) or {}
        plag_score_float = analysis.get("plagiarism_score", 0.0)
        plag_score_pct = int(round(plag_score_float * 100))
        total_sents = analysis.get("total_sentences", 0)
        plag_sents_count = analysis.get("plagiarized_sentences_count", 0)
        lexical_count = analysis.get("lexical_matches_count", 0)
        semantic_count = analysis.get("semantic_matches_count", 0)
        hybrid_count = analysis.get("hybrid_matches_count", 0)
        matches = analysis.get("matches", [])
        
        # Calculate percentages
        lexical_pct = int(round((lexical_count / total_sents) * 100)) if total_sents > 0 else 0
        semantic_pct = int(round((semantic_count / total_sents) * 100)) if total_sents > 0 else 0
        hybrid_pct = int(round((hybrid_count / total_sents) * 100)) if total_sents > 0 else 0
        original_pct = max(0, 100 - lexical_pct - semantic_pct - hybrid_pct)
        
        # Format current timestamp
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Group top reference sources
        sources_summary = {}
        for m in matches:
            ref = m.get("matched_sentence", {})
            if isinstance(ref, dict):
                doc_id = ref.get("doc_id", m.get("doc_id", "unknown"))
                doc_title = ref.get("doc_title", m.get("source", "Unknown Reference"))
                doc_author = ref.get("doc_author", m.get("source_author", "N/A"))
                doc_source = ref.get("doc_source", m.get("source_publication", "N/A"))
            else:
                doc_id = m.get("source", "unknown")
                doc_title = m.get("source", "Unknown Reference")
                doc_author = m.get("source_author", "N/A")
                doc_source = m.get("source_publication", "N/A")

            score = float(m.get("score", m.get("similarity", 0.0)))
            m_type = m.get("match_type", "lexical")
            
            if doc_id not in sources_summary:
                sources_summary[doc_id] = {
                    "title": doc_title,
                    "author": doc_author,
                    "source": doc_source,
                    "count": 0,
                    "max_score": 0.0,
                    "types": set()
                }
            sources_summary[doc_id]["count"] += 1
            sources_summary[doc_id]["max_score"] = max(sources_summary[doc_id]["max_score"], score)
            sources_summary[doc_id]["types"].add(m_type)
            
        sorted_sources = sorted(
            sources_summary.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        
        # Build the sources table HTML
        sources_table_rows = ""
        if sorted_sources:
            for idx, src in enumerate(sorted_sources, 1):
                types_str = " / ".join(list(src["types"])).upper()
                max_score_pct = int(round(src["max_score"] * 100))
                sources_table_rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>
                        <strong>{html.escape(src["title"])}</strong><br>
                        <span style="font-size: 8pt; color: #64748b;">{html.escape(src["author"])} — {html.escape(src["source"])}</span>
                    </td>
                    <td>{src["count"]}</td>
                    <td><span class="badge badge-{list(src["types"])[0]}">{types_str}</span></td>
                    <td><strong>{max_score_pct}%</strong></td>
                </tr>
                """
        else:
            sources_table_rows = """
            <tr>
                <td colspan="5" style="text-align: center; color: #64748b; padding: 20px;">
                    No plagiarism sources detected. Document is 100% original.
                </td>
            </tr>
            """
            
        # Reconstruct highlighted text
        highlighted_content = cls._get_highlighted_html(text, sentences, matches)
        
        # Build detailed matched segments comparison
        detailed_comparisons = ""
        if matches:
            for idx, m in enumerate(matches, 1):
                q_sent = m.get("query_sentence", {}).get("text", "") if isinstance(m.get("query_sentence"), dict) else str(m.get("query_text", ""))
                ms = m.get("matched_sentence", {})
                if isinstance(ms, dict):
                    r_sent = ms.get("text", "")
                    ref_title = ms.get("doc_title", "Reference Source")
                    ref_citation = f"{ms.get('doc_author', 'N/A')} — {ms.get('doc_source', 'N/A')}"
                else:
                    r_sent = str(ms)
                    ref_title = m.get("source", "Reference Source")
                    ref_citation = m.get("source_publication", "Reference Library")

                score_pct = int(round(float(m.get("score", m.get("similarity", 0.0))) * 100))
                m_type = m.get("match_type", "lexical")
                type_label = "Lexical Match" if m_type == "lexical" else ("Hybrid Match" if m_type == "hybrid" else "Semantic Match")
                badge_class = "badge-lexical" if m_type == "lexical" else ("badge-hybrid" if m_type == "hybrid" else "badge-semantic")
                
                detailed_comparisons += f"""
                <div class="match-item">
                    <div class="match-item-header">
                        <span class="match-item-title">Segment #{idx}</span>
                        <div>
                            <span class="badge {badge_class}">{type_label}</span>
                            <span class="badge {badge_class}">{score_pct}% Similarity</span>
                        </div>
                    </div>
                    <div class="match-item-body">
                        <div style="font-size: 8.5pt; color: #64748b; margin-bottom: 8px;">
                            <strong>Reference Source:</strong> {html.escape(ref_title)} ({html.escape(ref_citation)})
                        </div>
                        <div class="comparison-grid">
                            <div class="comparison-column">
                                <div class="comparison-label">Analyzed Text</div>
                                <blockquote class="comparison-text">{html.escape(q_sent)}</blockquote>
                            </div>
                            <div class="comparison-column">
                                <div class="comparison-label">Source Text</div>
                                <blockquote class="comparison-text">{html.escape(r_sent)}</blockquote>
                            </div>
                        </div>
                    </div>
                </div>
                """
        else:
            detailed_comparisons = """
            <div style="text-align: center; color: #64748b; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 30px;">
                No matches to break down.
            </div>
            """
            
        # Overall HTML Template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lemma Plagiarism Analysis Report</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm 15mm 20mm 15mm;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Outfit', 'Inter', 'Helvetica Neue', sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
            @bottom-left {{
                content: "Lemma Academic Integrity Platform";
                font-family: 'Outfit', 'Inter', 'Helvetica Neue', sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
        }}
        
        body {{
            font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
            color: #1e293b;
            line-height: 1.5;
            margin: 0;
            padding: 0;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Outfit', 'Helvetica Neue', Arial, sans-serif;
            color: #0f172a;
            margin-top: 0;
            font-weight: 700;
        }}

        .header {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}

        .header-title-container {{
            margin-bottom: 5px;
        }}

        .header-title {{
            font-size: 22pt;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            letter-spacing: -0.5px;
        }}

        .header-subtitle {{
            font-size: 8.5pt;
            color: #64748b;
            margin: 5px 0 0 0;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }}

        .meta-table {{
            width: 100%;
            margin-top: 15px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            border-collapse: separate;
            border-spacing: 15px 8px;
        }}

        .meta-label {{
            font-weight: 600;
            color: #475569;
            font-size: 9pt;
            width: 30%;
        }}

        .meta-value {{
            color: #0f172a;
            font-size: 9pt;
        }}

        .section {{
            margin-bottom: 30px;
        }}

        .section-title {{
            font-size: 13pt;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 6px;
            margin-bottom: 12px;
            font-weight: 700;
            color: #0f172a;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Metrics layout */
        .metrics-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 10px 0;
            margin-bottom: 20px;
        }}

        .metric-card {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            text-align: center;
            background-color: #ffffff;
            width: 20%;
        }}

        .metric-card.primary {{
            background-color: #0f172a;
            color: #ffffff;
            border-color: #0f172a;
        }}

        .metric-value {{
            font-size: 24pt;
            font-weight: 800;
            margin: 5px 0;
            font-family: 'Outfit', 'Helvetica Neue', Arial, sans-serif;
        }}

        .metric-label {{
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #64748b;
            font-weight: 600;
        }}

        .metric-card.primary .metric-label {{
            color: #94a3b8;
        }}

        /* Content highlighting */
        .content-box {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 15px;
            background-color: #ffffff;
            font-size: 10pt;
            text-align: justify;
        }}

        .mark-lexical {{
            background-color: #fee2e2;
            color: #991b1b;
            border-bottom: 1px solid #fca5a5;
        }}

        .mark-semantic {{
            background-color: #f3e8ff;
            color: #6b21a8;
            border-bottom: 1px solid #d8b4fe;
        }}

        .mark-hybrid {{
            background-color: #fef3c7;
            color: #92400e;
            border-bottom: 1px solid #fde68a;
        }}

        /* Tables */
        table.sources-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}

        table.sources-table th, table.sources-table td {{
            border: 1px solid #e2e8f0;
            padding: 8px 10px;
            text-align: left;
            font-size: 9pt;
        }}

        table.sources-table th {{
            background-color: #f1f5f9;
            font-weight: 700;
            color: #334155;
        }}

        table.sources-table tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 7.5pt;
            font-weight: 600;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-lexical {{
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }}

        .badge-semantic {{
            background-color: #f3e8ff;
            color: #6b21a8;
            border: 1px solid #d8b4fe;
        }}

        .badge-hybrid {{
            background-color: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }}

        /* Detailed Comparisons */
        .match-item {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            margin-bottom: 12px;
            background-color: #ffffff;
            page-break-inside: avoid;
        }}

        .match-item-header {{
            background-color: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            padding: 8px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .match-item-title {{
            font-size: 9pt;
            font-weight: 700;
            color: #334155;
            margin: 0;
        }}

        .match-item-body {{
            padding: 12px;
        }}

        .comparison-grid {{
            display: table;
            width: 100%;
            table-layout: fixed;
            margin-top: 5px;
        }}

        .comparison-column {{
            display: table-cell;
            width: 50%;
            vertical-align: top;
            padding-right: 10px;
        }}

        .comparison-column:last-child {{
            padding-right: 0;
            padding-left: 10px;
        }}

        .comparison-label {{
            font-weight: 600;
            color: #64748b;
            margin-bottom: 4px;
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .comparison-text {{
            background-color: #f8fafc;
            border: 1px solid #f1f5f9;
            border-radius: 4px;
            padding: 8px;
            margin: 0;
            font-style: italic;
            font-size: 8.5pt;
            color: #334155;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title-container">
            <h1 class="header-title">Academic Integrity & Plagiarism Analysis</h1>
            <div class="header-subtitle">Lemma Plagiarism Detection Engine</div>
        </div>
        <table class="meta-table">
            <tr>
                <td class="meta-label">Analyzed Document:</td>
                <td class="meta-value">{html.escape(filename)}</td>
                <td class="meta-label">Date Generated:</td>
                <td class="meta-value">{current_time}</td>
            </tr>
            <tr>
                <td class="meta-label">Total Characters:</td>
                <td class="meta-value">{char_count:,}</td>
                <td class="meta-label">Total Sentences:</td>
                <td class="meta-value">{sentence_count:,}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">Integrity Summary</div>
        <table class="metrics-table">
            <tr>
                <td class="metric-card primary">
                    <div class="metric-label">Plagiarism Score</div>
                    <div class="metric-value">{plag_score_pct}%</div>
                </td>
                <td class="metric-card">
                    <div class="metric-label">Lexical Matches</div>
                    <div class="metric-value" style="color: #ef4444;">{lexical_pct}%</div>
                    <div style="font-size: 7.5pt; color: #64748b;">{lexical_count} sentence(s)</div>
                </td>
                <td class="metric-card">
                    <div class="metric-label">Hybrid Matches</div>
                    <div class="metric-value" style="color: #f59e0b;">{hybrid_pct}%</div>
                    <div style="font-size: 7.5pt; color: #64748b;">{hybrid_count} sentence(s)</div>
                </td>
                <td class="metric-card">
                    <div class="metric-label">Semantic Matches</div>
                    <div class="metric-value" style="color: #8b5cf6;">{semantic_pct}%</div>
                    <div style="font-size: 7.5pt; color: #64748b;">{semantic_count} sentence(s)</div>
                </td>
                <td class="metric-card">
                    <div class="metric-label">Original Content</div>
                    <div class="metric-value" style="color: #10b981;">{original_pct}%</div>
                    <div style="font-size: 7.5pt; color: #64748b;">{total_sents - plag_sents_count} sentence(s)</div>
                </td>
            </tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">Top Reference Sources Matched</div>
        <table class="sources-table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 55%;">Source Document Details</th>
                    <th style="width: 12%;">Matches</th>
                    <th style="width: 16%;">Match Type</th>
                    <th style="width: 12%;">Max Sim</th>
                </tr>
            </thead>
            <tbody>
                {sources_table_rows}
            </tbody>
        </table>
    </div>

    <div class="page-break"></div>

    <div class="section">
        <div class="section-title">Document Content Analysis</div>
        <div class="content-box">
            {highlighted_content}
        </div>
    </div>

    <div class="page-break"></div>

    <div class="section">
        <div class="section-title">Segment-by-Segment Matching Breakdown</div>
        {detailed_comparisons}
    </div>
</body>
</html>
"""
        # Compile HTML string to PDF bytes via WeasyPrint, ReportLab, or HTML fallback
        if WEASYPRINT_AVAILABLE and HTML is not None:
            try:
                pdf_bytes = io.BytesIO()
                HTML(string=html_content).write_pdf(target=pdf_bytes)
                return pdf_bytes.getvalue()
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"WeasyPrint render failed: {e}. Using ReportLab fallback.")

        # Fallback to ReportLab PDF generator
        return PDFGeneratorService.generate_reportlab_pdf(data)

    @staticmethod
    def generate_html_report(result_data: dict) -> str:
        """Returns the full HTML markup for the report."""
        # Use existing logic to generate HTML
        filename = result_data.get("filename", "document.txt")
        char_count = result_data.get("char_count", 0)
        sentence_count = result_data.get("sentence_count", 0)
        sentences = result_data.get("sentences", [])
        
        analysis = result_data.get("analysis", {})
        plag_score = analysis.get("plagiarism_score", 0.0)
        def extract_text_str(val):
            if isinstance(val, dict):
                return val.get("text", "")
            return str(val or "")

        def format_match_item(m):
            query_str = extract_text_str(m.get("query_sentence"))
            ref_data = m.get("matched_sentence")
            ref_str = extract_text_str(ref_data) if not isinstance(ref_data, dict) else ref_data.get("text", "")
            
            flagged = query_str or ref_str or "Flagged sentence fragment"
            
            src_name = m.get("source") or "Reference Document"
            if isinstance(ref_data, dict) and ref_data.get("doc_title"):
                src_name = f"{ref_data.get('doc_title')} ({ref_data.get('doc_author', 'Unknown')})"
                
            sim_val = m.get("score") if m.get("score") is not None else m.get("similarity", 0.0)
            sim_pct = round(sim_val * 100, 1) if sim_val <= 1.0 else round(sim_val, 1)
            
            return f'<div class="match-item"><p><strong>Flagged Sentence:</strong> {html.escape(flagged)}</p><p><strong>Source:</strong> {html.escape(src_name)} ({sim_pct}% match)</p></div>'

        matches_html = "".join([format_match_item(m) for m in matches]) if matches else "<p>No matching passages flagged.</p>"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Lemma Integrity Report - {html.escape(filename)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f8fafc; }}
.card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
.badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 14px; }}
.badge-danger {{ background: #fee2e2; color: #991b1b; }}
.badge-success {{ background: #dcfce7; color: #166534; }}
.match-item {{ border-left: 4px solid #ef4444; padding: 12px; margin-bottom: 12px; background: #fff1f2; }}
</style>
</head>
<body>
<div class="card">
  <h1>LEMMA INTEGRITY REPORT</h1>
  <p><strong>Document:</strong> {html.escape(filename)} | <strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <hr>
  <h2>Plagiarism Score: <span class="badge badge-danger">{plag_score}%</span> &nbsp; Originality: <span class="badge badge-success">{orig_score}%</span></h2>
  <p><strong>Total Sentences:</strong> {sentence_count} | <strong>Total Characters:</strong> {char_count:,} | <strong>Flagged Sentences:</strong> {len(matches)}</p>
</div>
<div class="card">
  <h3>Flagged Matches</h3>
  {matches_html}
</div>
</body>
</html>"""

    @staticmethod
    def generate_reportlab_pdf(result_data: dict) -> bytes:
        """Generates clean standalone PDF using ReportLab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=20,
                textColor=colors.HexColor("#4f46e5"),
                spaceAfter=6
            )
            subtitle_style = ParagraphStyle(
                'SubStyle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                textColor=colors.HexColor("#64748b"),
                spaceAfter=15
            )
            heading_style = ParagraphStyle(
                'HeadingStyle',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=13,
                textColor=colors.HexColor("#1e293b"),
                spaceBefore=12,
                spaceAfter=8
            )
            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#334155")
            )
            flagged_style = ParagraphStyle(
                'FlaggedStyle',
                parent=styles['Normal'],
                fontName='Helvetica-Oblique',
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#991b1b")
            )

            filename = result_data.get("filename", "Uploaded Document")
            analysis = result_data.get("analysis", {})
            plag_score = analysis.get("plagiarism_score", 0.0)
            orig_score = analysis.get("originality_score", 100.0)
            char_count = result_data.get("char_count", len(result_data.get("text", "")))
            sentence_count = result_data.get("sentence_count", len(result_data.get("sentences", [])))
            matches = analysis.get("matches", [])
            sources = analysis.get("sources", [])

            # Header
            story.append(Paragraph("LEMMA INTEGRITY REPORT", title_style))
            story.append(Paragraph(f"Official Plagiarism & Originality Verification Document • Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=15))

            # Metadata Table
            meta_data = [
                [Paragraph("<b>Target Document:</b>", body_style), Paragraph(str(filename), body_style),
                 Paragraph("<b>Total Characters:</b>", body_style), Paragraph(f"{char_count:,}", body_style)],
                [Paragraph("<b>Plagiarism Score:</b>", body_style), Paragraph(f"<b>{plag_score}%</b>", body_style),
                 Paragraph("<b>Originality Score:</b>", body_style), Paragraph(f"<b>{orig_score}%</b>", body_style)],
                [Paragraph("<b>Total Sentences:</b>", body_style), Paragraph(f"{sentence_count:,}", body_style),
                 Paragraph("<b>Flagged Sentences:</b>", body_style), Paragraph(f"{len(matches)}", body_style)]
            ]
            t = Table(meta_data, colWidths=[110, 150, 110, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 15))

            # Top Sources
            if sources:
                story.append(Paragraph("Top Matched Reference Sources", heading_style))
                src_data = [[Paragraph("<b>#</b>", body_style), Paragraph("<b>Title & Authors</b>", body_style), Paragraph("<b>Similarity</b>", body_style), Paragraph("<b>Matches</b>", body_style)]]
                for idx, s in enumerate(sources[:5], 1):
                    sim = f"{round(s.get('max_similarity', 0.0)*100, 1)}%" if s.get('max_similarity') else "N/A"
                    src_data.append([
                        Paragraph(str(idx), body_style),
                        Paragraph(f"<b>{s.get('title', 'Unknown')}</b><br/><font color='#64748b'>{s.get('author', 'N/A')}</font>", body_style),
                        Paragraph(sim, body_style),
                        Paragraph(f"{s.get('match_count', 1)}", body_style)
                    ])
                st = Table(src_data, colWidths=[25, 345, 80, 70])
                st.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#c7d2fe")),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(st)
                story.append(Spacer(1, 15))

            # Flagged matches list
            story.append(Paragraph("Flagged Sentence Analysis", heading_style))
            if matches:
                for idx, m in enumerate(matches[:8], 1):
                    q_text = m.get("matched_sentence") or m.get("query_sentence", {}).get("text", "") or m.get("query_text", "")
                    src = m.get("source", m.get("doc_title", "Reference Source"))
                    sim = round(m.get("similarity", 0) * 100, 1)
                    story.append(Paragraph(f"<b>{idx}. Flagged ({sim}% similarity) — Source: {src}</b>", body_style))
                    story.append(Paragraph(f"\"{q_text}\"", flagged_style))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No sentences were flagged for plagiarism in this document.", body_style))

            # Build PDF
            doc.build(story)
            return buffer.getvalue()

        except Exception as e:
            # Absolute fallback if ReportLab fails
            return PDFGeneratorService.generate_html_report(result_data).encode("utf-8")

