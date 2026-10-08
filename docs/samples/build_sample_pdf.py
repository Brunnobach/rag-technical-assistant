"""Build the original sample PDF committed under docs/samples/."""

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "anaerobic-digestion-notes.md"
OUTPUT = ROOT / "anaerobic-digestion-notes.pdf"

BODY = SOURCE.read_text(encoding="utf-8")
# Helvetica core fonts are Latin-1; keep the sample readable without extra TTF files.
BODY = (
    BODY.replace("°C", " deg C")
    .replace("³", "3")
    .replace("—", "-")
    .replace("–", "-")
)


class NotePDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80)
        self.cell(0, 8, "RAG Technical Assistant - original sample (MIT)", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def main() -> None:
    pdf = NotePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_text_color(20)
    for raw_line in BODY.splitlines():
        line = raw_line.rstrip()
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 9, line[2:])
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 7, line[3:])
            pdf.ln(1)
        elif line.strip() == "":
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6.5, line)
    pdf.output(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
