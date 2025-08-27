import hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors

def create_certificate(organization_name, organization_address, 
                           competency, accreditation_no, 
                           date_accredited, expiration_date, 
                           filename):
    """
    Creates a TESDA-like Certificate of Accreditation PDF
    
    Args:
        organization_name (str): Name of the accredited organization
        organization_address (str): Address of the organization
        competency (str): The competency being accredited (e.g., "FOOD AND BEVERAGE SERVICES NC II")
        accreditation_no (str): Accreditation number
        date_accredited (str): Date of accreditation
        expiration_date (str): Expiration date
        filename (str): Output PDF filename
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Set up margins and spacing
    left_margin = 20 * mm
    top_margin = height - 30 * mm
    line_spacing = 6 * mm
    
    # Add TESDA header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, top_margin, "TESDA, v.")
    c.drawString(left_margin, top_margin - line_spacing, "Rev. N=17")
    c.drawString(left_margin, top_margin - 2*line_spacing, "TESDA")
    c.drawString(left_margin, top_margin - 3*line_spacing, "1.750/1A")
    
    # Add main title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, top_margin - 5*line_spacing, 
                       "TECHNICAL EDUCATION AND SKILLS DEVELOPMENT AUTHORITY")
    
    # Add certificate title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, top_margin - 7*line_spacing, 
                       "CERTIFICATE OF ACCREDITATION")
    
    # Add certificate body
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, top_margin - 9*line_spacing, "This is to certify that")
    
    # Organization name (bold and centered)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, top_margin - 11*line_spacing, organization_name.upper())
    
    # Organization address
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, top_margin - 12*line_spacing, organization_address.upper())
    
    # Accreditation details
    c.drawCentredString(width/2, top_margin - 14*line_spacing, "is an Accredited Competency Assessment Center for")
    
    # Competency (bold)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, top_margin - 16*line_spacing, competency.upper())
    
    # Accreditation number
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, top_margin - 18*line_spacing, f"Accreditation No. {accreditation_no}")
    
    # Dates
    c.drawCentredString(width/2, top_margin - 20*line_spacing, f"Date Accredited: {date_accredited}")
    c.drawCentredString(width/2, top_margin - 21*line_spacing, f"Expiration Date: {expiration_date}")
    
    # Approved by section
    c.drawCentredString(width/2, top_margin - 25*line_spacing, "Approved by:")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, top_margin - 26*line_spacing, "DORIE U. GUTIERREZ")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, top_margin - 27*line_spacing, "Acting Regional Director, TESDA Region IV-A")
    
    c.save()

def get_certificate_hash(filename):
    """Generates a SHA-256 hash of the certificate file"""
    with open(filename, "rb") as f:
        file_content = f.read()
        return "0x" + hashlib.sha256(file_content).hexdigest()

# Example usage:
create_certificate(
    organization_name="LAGUNA SINO-FILIPINO EDUCATIONAL FOUNDATION INC.",
    organization_address="229 A.MABINI ST. POBLACION II STA. CRUZ, LAGUNA",
    competency="FOOD AND BEVERAGE SERVICES NC II",
    accreditation_no="AC-FB80204342425284",
    date_accredited="28 December 2024",
    expiration_date="28 December 2026",
    filename="tesda_certificate.pdf"
)

print(f"Certificate hash: {get_certificate_hash('tesda_certificate.pdf')}")