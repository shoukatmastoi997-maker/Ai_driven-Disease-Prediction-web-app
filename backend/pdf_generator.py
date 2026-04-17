import io
from typing import Any

from fpdf import FPDF
from fastapi.responses import StreamingResponse

from backend.utils import risk_guidance


def generate_pdf_report(record: dict[str, Any]) -> StreamingResponse:
    """Generate PDF report for a prediction record."""
    top_predictions = record["top_predictions"]
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Disease Prediction Report", ln=True)
    
    # Record info
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Record ID: {record['id']}", ln=True)
    pdf.cell(0, 8, f"Generated at: {record['created_at']}", ln=True)
    pdf.ln(3)
    
    # Patient details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Patient Details", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Name: {record['name']}", ln=True)
    pdf.cell(0, 8, f"Father Name: {record['fname']}", ln=True)
    pdf.cell(0, 8, f"Age: {record['age']}", ln=True)
    pdf.cell(0, 8, f"Gender: {record['gender']}", ln=True)
    if record["basic_info"]:
        pdf.multi_cell(0, 8, f"Basic Info: {record['basic_info']}")
    pdf.ln(2)
    
    # Prediction summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Prediction Summary", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Predicted Disease: {record['predicted_disease']}", ln=True)
    pdf.cell(0, 8, f"Risk Level: {record['risk_level']}", ln=True)
    pdf.cell(0, 8, f"Confidence: {record['confidence'] * 100:.2f}%", ln=True)
    pdf.multi_cell(0, 8, f"Guidance: {risk_guidance(record['risk_level'])}")
    pdf.ln(2)
    
    # Symptoms
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Symptoms", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, ", ".join(record["symptoms"]))
    pdf.ln(2)
    
    # Top predictions
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Top Predictions", ln=True)
    pdf.set_font("Arial", "", 11)
    for item in top_predictions:
        pdf.cell(0, 8, f"- {item['disease']}: {item['percent']:.2f}%", ln=True)
    
    # Render PDF
    rendered = pdf.output(dest="S")
    if isinstance(rendered, (bytes, bytearray)):
        content = bytes(rendered)
    else:
        content = str(rendered).encode("latin-1")
    
    filename = f"prediction_report_{record['id']}.pdf"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )