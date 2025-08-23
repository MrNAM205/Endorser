import json
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def attach_endorsement_to_pdf_function(original_pdf_path, endorsement_data, output_pdf_path, ink_color, page_index):
    # Create overlay PDF with endorsement text
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 12)
    can.drawString(50, 750, "🔗 Endorsement Chain Attached")

    can.setFont("Helvetica", 10)
    y = 730
    for i, e in enumerate(endorsement_data.get("endorsements", []), start=1):
        can.drawString(50, y, f"{i}. {e['endorser_name']} → {e['next_payee']}")
        y -= 15
        can.drawString(60, y, f"Text: {e['text']}")
        y -= 15
        can.drawString(60, y, f"Signature: {e['signature'][:60]}...")
        y -= 25

    sig = endorsement_data.get("signature_block", {})
    can.drawString(50, y, f"Signed by: {sig.get('signed_by')} ({sig.get('capacity')})")
    y -= 15
    can.drawString(60, y, f"Signature: {sig.get('signature')}")
    y -= 15
    can.drawString(60, y, f"Date: {sig.get('date')}")
    can.save()
    packet.seek(0)

    # Load original PDF
    reader = PdfReader(original_pdf_path)
    writer = PdfWriter()
    overlay = PdfReader(packet)

    # Merge overlay onto specified page
    page = reader.pages[page_index]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    # Add remaining pages
    for i, p in enumerate(reader.pages):
        if i != page_index:
            writer.add_page(p)

    # Save new PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    print(f"📎 Endorsement chain attached to {output_pdf_path}")
