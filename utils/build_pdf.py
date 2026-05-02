def sanitize(text: str) -> str:
    replacements = {
        "\u2018": "'", "\u2019": "'", # curly apostrophes
        "\u201c": '"', "\u201d": '"', # curly quotes
        "\u2013": "-", "\u2014": "--", # en/em dash
        "\u2022": "*", # bullet
        "\u2026": "...", # ellipsis
        "\u00b7": "*", # middle dot
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

def build_pdf(goal: str, result: dict, report_depth) -> bytes:
    from fpdf import FPDF
    import io, matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "AI Business Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, sanitize(f"Goal: {goal}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, sanitize(f"Generated: {result['timestamp']}  |  Depth: {report_depth}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Chart
    cd = result.get("chart_data")
    if cd:
        try:
            fig, ax = plt.subplots(figsize=(6, 3), facecolor="#080b10")
            ax.set_facecolor("#080b10")
            if cd["type"] == "pie":
                ax.pie(cd["values"], labels=cd["labels"], autopct="%1.0f%%",
                       colors=["#3b82f6","#60a5fa","#93c5fd","#bfdbfe","#1d4ed8"])
            else:
                ax.bar(cd["labels"], cd["values"], color="#3b82f6")
                ax.tick_params(colors="white")
                for spine in ax.spines.values():
                    spine.set_edgecolor("#1a2740")
            ax.set_title(cd.get("title", ""), color="white", fontsize=10)
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            import tempfile, os as _os
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(buf.read())
                tmp_path = tmp.name
            pdf.image(tmp_path, w=160)
            _os.unlink(tmp_path)
            pdf.ln(4)
        except Exception:
            pass

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Search Queries", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for i, q in enumerate(result["queries"], 1):
        pdf.cell(0, 7, sanitize(f"{i}. {q}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Strategic Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 7, sanitize(result["report"]))

    return bytes(pdf.output())