import win32print
import win32api
import os
from jinja2 import Environment, FileSystemLoader
from html2image import Html2Image
from PIL import Image
import shutil
from sqlalchemy import create_engine
import hashlib
import random
import string
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Setup MySQL connection
db_config = {
    'user': os.environ.get('db_user'),
    'password': os.environ.get('db_password'),
    'host': os.environ.get('db_host'),
    'database': os.environ.get('db_name'),
    'port': os.environ.get('db_port'),
    'autocommit':True,
}


DATABASE_URL = f"mysql://{os.environ.get('db_user')}:{os.environ.get('db_password')}@{os.environ.get('db_host')}:{os.environ.get('db_port')}/{os.environ.get('db_name')}"
engine = create_engine(DATABASE_URL)

# cnx = mysql.connector.connect(**db_config)


def print_zebra(zpl_data=None, printer_name='zebra'):
    # Open the printer
    hprinter = win32print.OpenPrinter(printer_name)
    try:
        # Start the print job
        pdc = win32print.StartDocPrinter(hprinter, 1, ("ZPL Document", None, "RAW"))

        # Send raw data to the printer
        win32print.WritePrinter(hprinter, zpl_data.encode())

        # End the print job
        win32print.EndDocPrinter(hprinter)
    finally:
        win32print.ClosePrinter(hprinter)


def print_document(filename, printer_name="EPSON25CEF5 (ET-2810 Series)"):
    if printer_name is None:
        printer_name = win32print.GetDefaultPrinter()
    
    # Set the printer to the specified one
    win32print.SetDefaultPrinter(printer_name)
    
    # Use the Windows shell to print the document
    win32api.ShellExecute(0, "print", filename, None, ".", 0)



def random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def generate_random_hash():
    random_data = random_string()
    result = hashlib.sha256(random_data.encode()).hexdigest()
    return result



def images_to_pdf(img_path, output_dir='temp', repetition=1):

    # Create a list to store the images
    img_list = []


    img = Image.open(img_path).convert('RGB')
    
    # Append the image to the list the specified number of times
    for _ in range(repetition):
        img_list.append(img)

    # Save images to a single PDF
    if img_list:
        output_path = os.path.join(output_dir, f"{os.path.splitext(img_path)[0].split('/')[1]}.pdf")
        img_list[0].save(output_path, save_all=True, append_images=img_list[1:])
        print(f"PDF saved at {output_path}")
    else:
        print("No image files found in the folder.")

def delete_directory(directory_path):
    try:
        shutil.rmtree(directory_path)
        print(f"Directory '{directory_path}' has been deleted.")
    except Exception as e:
        print(f"Error: {e}")

def create_directory_if_not_exists(directory_path):
    """
    Creates the specified directory if it doesn't exist.

    Args:
    - directory_path (str): The path to the directory to create.

    Returns:
    - None
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)




def pdf_render_print(order_id, folder_path="temp"):
    create_directory_if_not_exists(folder_path)

    if not order_id:
        return None


    query = f"""
            SELECT 
                o.id AS order_id, 
                o.customer AS store, 
                c.address AS address,
                c.company AS customer,
                c.phone AS phone,
                o.date, 
                o.product, 
                COALESCE(o.price * 1.14, 0) AS price, 
                o.quantity AS weight, 
                w.quantity AS delivered
            FROM 
                salmon_orders o
            LEFT JOIN 
                salmon_order_weight w ON o.id = w.order_id
            LEFT JOIN 
                salmon_customer c ON o.customer = c.customer
            WHERE
                o.id = {order_id};
        """

    df = pd.read_sql(query, engine)
    df['expiry_date'] = df['date'] + pd.Timedelta(days=6)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])

    df['date'] = df['date'].dt.strftime("%Y-%m-%d, %a")
    df['expiry_date'] = df['expiry_date'].dt.strftime("%Y-%m-%d, %a")
    # Convert to desired JSON structure
    delivery_note_data = {}
    for column in df.columns:
        if column == 'delivered' and len(df)>1:
            delivery_note_data[column] = df[column].sum()
        else:
            delivery_note_data[column] = df[column].iloc[0]



    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/salmon_delivery_template.html')

    rendered_html = template.render(delivery_note_data)
    hti = Html2Image(
        size=(2142, 3000),
        # custom_flags=['--no-sandbox', '--headless', '--disable-gpu', '--disable-software-rasterizer', '--disable-dev-shm-usage'],
        output_path=folder_path
        )
    # hti.browser_executable = "/usr/bin/google-chrome"
    random_hash = generate_random_hash()
    
    image_name = f'{random_hash}.png'
    image_path = f'{folder_path}/{image_name}'
    hti.screenshot(html_str=rendered_html, save_as=image_name)
    images_to_pdf(image_path, output_dir='temp', repetition=2)
    if os.path.isfile(os.path.join(folder_path, f"{random_hash}.pdf")):
        print_document(os.path.join(folder_path, f"{random_hash}.pdf"))
    else:
        print(f"Print failed due to unable to generate PDF file.")



zpl_data = """^XA  ; Start of label

; Draw a box (border) around the label
^FO20,20^GB750,500,4^FS

; Add a title text
^FO50,50^A0N,70,70^FDZebra Label^FS

; Add a subtitle text
^FO50,150^A0N,40,40^FDComplex Design Example^FS

; Draw a line separator
^FO50,210^GB700,4,4^FS

; Add a barcode (Code 128 with value '12345678')
^FO100,250^BY3^BCN,100,Y,N,N^FD12345678^FS

; Add text below the barcode
^FO100,380^A0N,40,40^FDScan the barcode above^FS

; Add a QR code with value 'https://www.zebra.com'
^FO500,250^BQN,2,10^FDQA,https://www.zebra.com^FS

; Add text next to the QR code
^FO500,400^A0N,40,40^FDVisit Zebra's Website^FS  

^XZ  ; End of label
"""
