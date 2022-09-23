from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

packet = io.BytesIO()
can = canvas.Canvas(packet, pagesize=letter)
can.drawString(400, 320, "Full saaaa", mode=2)
can.drawString(400, 350, "K n-", mode=1)
can.drawString(320, 290, "start date dan     finish date gacha")
can.drawString(280, 270, "{{mavzu}} mavzusi bo’yicha 40 soatlik maxsus o’quv kursini")
can.drawString(350, 250, "muvaffaqiyatli tamomladi")
can.drawString(300, 120, "create_at")
can.drawString(550, 120, "no_2")
can.drawInlineImage("/home/diyorbek/Documents/projects/uzarxiv/static/qr_code.png", 630, 140, width=90, height=90)
can.setFontSize(size=25)
can.save()

#move to the beginning of the StringIO buffer
packet.seek(0)

# create a new PDF with Reportlab
new_pdf = PdfFileReader(packet)
# read your existing PDF
existing_pdf = PdfFileReader(open("../static/certificate.pdf", "rb"))
output = PdfFileWriter()
# add the "watermark" (which is the new pdf) on the existing page
page = existing_pdf.getPage(0)
page.mergePage(new_pdf.getPage(0))
output.addPage(page)
# finally, write "output" to a real file
outputStream = open("../static/result.pdf", "wb")
output.write(outputStream)
outputStream.close()