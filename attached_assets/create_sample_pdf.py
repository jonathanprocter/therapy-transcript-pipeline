import PyPDF2
from PyPDF2 import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Create a PDF with text content
def create_sample_pdf(output_path, client_name="John Smith", date="2025-06-04"):
    # First create a PDF with reportlab (with actual text content)
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, f"Therapy Session Transcript: {client_name}")
    c.setFont("Helvetica", 12)
    c.drawString(72, 730, f"Date: {date}")
    c.drawString(72, 710, "Therapist: Dr. Jane Wilson")
    
    # Add content
    c.setFont("Helvetica", 11)
    y_position = 670
    
    lines = [
        "",
        "Dr. Wilson: Hello John, how are you feeling today?",
        "",
        f"{client_name}: I've been having some trouble with anxiety this week, especially at work.",
        "",
        "Dr. Wilson: I'm sorry to hear that. Can you tell me more about what's been happening?",
        "",
        f"{client_name}: There's been a lot of pressure with deadlines, and I've been having trouble sleeping.",
        "I find myself worrying about work even when I'm at home trying to relax.",
        "",
        "Dr. Wilson: That sounds difficult. Let's talk about some anxiety management techniques we",
        "discussed last time. Have you been practicing the breathing exercises?",
        "",
        f"{client_name}: I tried them a few times, but it's hard to remember when I'm in the moment.",
        "",
        "Dr. Wilson: That's understandable. It takes practice to make these techniques habitual.",
        "Let's go through them again and discuss how you might incorporate them into your daily routine.",
        "",
        f"{client_name}: That would be helpful. I really want to make progress on this.",
        "",
        "Dr. Wilson: I appreciate your commitment. Let's also review your personal goals from last session",
        "and see what progress you've made and what challenges you've encountered."
    ]
    
    for line in lines:
        c.drawString(72, y_position, line)
        y_position -= 15
    
    c.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    
    # Create a new PDF with Reportlab content
    new_pdf = PyPDF2.PdfReader(packet)
    
    # Create output PDF
    output = PdfWriter()
    
    # Add page from the new PDF
    output.add_page(new_pdf.pages[0])
    
    # Add metadata
    output.add_metadata({
        '/Title': f'Therapy Session - {client_name} - {date}',
        '/Author': 'Dr. Jane Wilson',
        '/Subject': 'Therapy Session Transcript',
        '/Keywords': 'therapy, anxiety, counseling'
    })
    
    # Write the output PDF
    with open(output_path, 'wb') as output_file:
        output.write(output_file)
    
    print(f"Sample PDF created successfully at {output_path}")

if __name__ == "__main__":
    create_sample_pdf("test_files/John_Smith_2025-06-04.pdf")
