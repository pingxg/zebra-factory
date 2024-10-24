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
        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
                source_html,
                dest=result_file)
    # return error status
    return pisa_status.err

def generate_delivery_note(date, customer=None):
    # get data for the PDF
    data = get_data_for_pdf(date, customer)

    # check if temp directory exists
    if os.path.exists(os.path.join(os.getcwd(), "temp")):
        # Remove the directory and all its contents
        shutil.rmtree(os.path.join(os.getcwd(), "temp"))

    # create temp directory if it does not exist
    if not os.path.exists(os.path.join(os.getcwd(), "temp")):
        os.makedirs(os.path.join(os.getcwd(), "temp"))
    
    if data:
        # iterate over data and generate PDFs
        for i in range(len(data)):
            # render HTML content for the PDF
            html_content = render_template('deliverynote/delivery_note_template.html', data=data[i])
            # generate PDF file name
            pdf_file_name = f"{date}_{customer}.pdf" if customer else f"{date}_{i:03d}.pdf"
            # generate PDF file path
            pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
            # convert HTML to PDF
            convert_html_to_pdf(html_content, pdf_file_path)
        
        matching_files = []
        if customer is None:
            # Regular expression pattern to match 'yyyy-mm-dd_{index}'
            pattern = r'^\d{4}-\d{2}-\d{2}_\d+.pdf$'
            # List to store matching file paths
            
            # Iterate through files in the directory
            for filename in os.listdir("temp"):
                if re.match(pattern, filename):
                    full_path = os.path.join("temp", filename)
                    matching_files.append(full_path)

            # generate final PDF file name
            pdf_file_name = f"{date}.pdf"
        else:
            # add single PDF file to matching files
            matching_files.append(os.path.join("temp", pdf_file_name))

        # create PDF writer
        writer = PdfWriter()
        # generate final PDF file path
        pdf_file_path = os.path.join(os.getcwd(), "temp", pdf_file_name)
        # add pages from all matching files to the writer
        for inpfn in sorted(matching_files):
            writer.addpages(PdfReader(inpfn).pages)
        # write the final PDF
        writer.write(pdf_file_path)
    else:
        # return False if no data
        return False
    # return final PDF file path
    return pdf_file_path
