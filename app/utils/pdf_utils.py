
import os
import re
import shutil
from xhtml2pdf import pisa
from pdfrw import PdfReader, PdfWriter
from flask import render_template
from ..services.pdf_service import get_data_for_pdf

def convert_html_to_pdf(source_html, output_filename):
    # open output file for writing (truncated binary)
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(
                source_html,
                dest=result_file)
    return pisa_status.err

def generate_delivery_note(date, customer=None):
    data = get_data_for_pdf(date, customer)

    if os.path.exists(os.path.join(os.getcwd(), "temp")):
        # Remove the directory and all its contents
        shutil.rmtree(os.path.join(os.getcwd(), "temp"))

    if not os.path.exists(os.path.join(os.getcwd(), "temp")):
        os.makedirs(os.path.join(os.getcwd(), "temp"))
    
    if data:
        for i in range(len(data)):
            html_content = render_template('printing/delivery_note_template.html', data=data[i])
            pdf_file_name = f"{date}_{customer}.pdf" if customer else f"{date}_{i:03d}.pdf"
            pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
            convert_html_to_pdf(html_content, pdf_file_path)
        matching_files = []
        if customer is None:
            # Regular expression pattern to match 'yyyy-mm-dd_{index}'
            pattern = r'^\d{4}-\d{2}-\d{2}_\d+.pdf$'
            # List to store matching file paths
            
            # Iterate through files in the directory
            for filename in os.listdir("temp" ):
                if re.match(pattern, filename):
                    full_path = os.path.join("temp", filename)
                    matching_files.append(full_path)
                    matching_files.append(full_path)

            pdf_file_name = f"{date}.pdf"
        else:
            matching_files.append(os.path.join("temp", pdf_file_name))
            matching_files.append(os.path.join("temp", pdf_file_name))

        writer = PdfWriter()
        pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
        for inpfn in sorted(matching_files):
            writer.addpages(PdfReader(inpfn).pages)
        writer.write(pdf_file_path)
    else:
        return False
    return pdf_file_path
