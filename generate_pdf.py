import os
import re
from fpdf import FPDF

def sanitize_text(text):
    if not text:
        return ""
    # Replace unicode special dashes, quotes, and symbols with latin-1 equivalents
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "≤": "<=",
        "≥": ">=",
        "→": "->",
        "•": "*",
        "\u200b": "",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Encode to latin-1 replacing unencodable chars
    return text.encode("latin-1", "replace").decode("latin-1")

class TechnicalReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        t1 = sanitize_text("Escuela Politécnica Nacional - ICCD753 Recuperación de Información")
        t2 = sanitize_text("Informe Técnico RAG Multimodal")
        self.cell(110, 8, t1, border=0, new_x="RIGHT", new_y="TOP", align="L")
        self.cell(70, 8, t2, border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_draw_color(200, 200, 200)
        self.line(15, 18, 195, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

def markdown_to_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    pdf = TechnicalReportPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 20, 15)
    pdf.add_page()

    lines = text.split("\n")
    in_code_block = False
    in_table = False
    table_data = []

    for line in lines:
        line_str = line.strip()

        # Code block handling
        if line_str.startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                pdf.ln(2)
            continue

        if in_code_block:
            pdf.set_font("Courier", "", 8)
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(40, 40, 40)
            clean_code = sanitize_text(f"  {line}")
            pdf.cell(0, 4.5, clean_code, new_x="LMARGIN", new_y="NEXT", fill=True)
            continue

        # Table handling
        if "|" in line_str and line_str.startswith("|") and line_str.endswith("|"):
            if "---" in line_str:
                continue
            cols = [c.strip() for c in line_str.split("|")[1:-1]]
            table_data.append(cols)
            in_table = True
            continue
        elif in_table:
            # Render table
            if table_data:
                pdf.ln(3)
                col_widths = [30, 45, 45, 45] if len(table_data[0]) == 4 else [165 // len(table_data[0])] * len(table_data[0])
                
                # Header
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(30, 41, 59)
                pdf.set_text_color(255, 255, 255)
                for idx, cell_text in enumerate(table_data[0]):
                    clean_cell = sanitize_text(re.sub(r'[\*\$\\_]', '', cell_text))
                    pdf.cell(col_widths[idx], 7, clean_cell, border=1, align="C", fill=True)
                pdf.ln()

                # Rows
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(30, 30, 30)
                for r_idx, row in enumerate(table_data[1:]):
                    bg_color = (245, 247, 250) if r_idx % 2 == 0 else (255, 255, 255)
                    pdf.set_fill_color(*bg_color)
                    for idx, cell_text in enumerate(row):
                        clean_cell = sanitize_text(re.sub(r'[\*\$\\_]', '', cell_text))
                        width = col_widths[idx] if idx < len(col_widths) else 30
                        pdf.cell(width, 6.5, clean_cell, border=1, align="C", fill=True)
                    pdf.ln()
                pdf.ln(3)
            table_data = []
            in_table = False

        if not line_str:
            pdf.ln(2)
            continue

        # Main Title H1
        if line_str.startswith("# "):
            title = sanitize_text(line_str.replace("# ", "").strip())
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(15, 23, 42)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 9, title)
            pdf.set_draw_color(15, 23, 42)
            pdf.set_line_width(0.5)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.set_line_width(0.2)
            pdf.ln(4)
            continue

        # Subtitle H2
        if line_str.startswith("## "):
            title = sanitize_text(line_str.replace("## ", "").strip())
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(3)
            pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            continue

        # Subtitle H3
        if line_str.startswith("### "):
            title = sanitize_text(line_str.replace("### ", "").strip())
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(51, 65, 85)
            pdf.ln(2)
            pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
            continue

        # Bullet points
        if line_str.startswith("* ") or line_str.startswith("- "):
            bullet_text = line_str[2:].strip()
            clean_text = sanitize_text(re.sub(r'\*\*(.*?)\*\*', r'\1', bullet_text))
            clean_text = re.sub(r'[\$\\]', '', clean_text)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(40, 40, 40)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, f"- {clean_text}")
            pdf.ln(1)
            continue

        # Normal text / Metadata
        clean_text = sanitize_text(re.sub(r'\*\*(.*?)\*\*', r'\1', line_str))
        clean_text = re.sub(r'[\$\\]', '', clean_text)
        
        if "Asignatura:" in clean_text or "Integrantes:" in clean_text or "Institución:" in clean_text:
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.set_text_color(71, 85, 105)
            pdf.set_x(pdf.l_margin)
            pdf.cell(0, 5, clean_text, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, clean_text)

    pdf.output(pdf_path)
    print(f"PDF generado exitosamente en: {pdf_path}")

if __name__ == "__main__":
    md_file = "/Users/alexander/Documents/EPN/Recuperacion de Información/ProyectoFinal/INFORME.md"
    pdf_file = "/Users/alexander/Documents/EPN/Recuperacion de Información/ProyectoFinal/INFORME.pdf"
    markdown_to_pdf(md_file, pdf_file)
