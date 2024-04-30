import win32print
import win32api
import os
from jinja2 import Environment, FileSystemLoader
from html2image import Html2Image
from PIL import Image
import shutil
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import hashlib
import random
import string
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Setup MySQL connection
db_config = {
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME'),
    'port': os.environ.get('DB_PORT'),
    'autocommit':True,
}


DATABASE_URL = f"mysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def print_zebra(zpl_data=None, printer_name=os.environ.get('ZEBRA_PRINTER_NAME')):
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



def print_document(pdf_path, printer_name=os.environ.get('DEFAULT_PRINTER_NAME')):
    # Path to Adobe Reader or Adobe Acrobat. Adjust if it's located differently on your system.
    acrobat_path = os.environ.get('ACROBAT_PATH')

    # Command to send to the shell
    cmd = f'"{acrobat_path}" /N /T "{pdf_path}" "{printer_name}"'

    win32api.WinExec(cmd)


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


def pdf_render_print(order_id, file_type, folder_path="temp"):
    create_directory_if_not_exists(folder_path)
    if not order_id:
        return None
    query = text("""
            SELECT 
                o.id AS order_id, 
                o.customer AS store, 
                c.address AS address,
                c.company AS customer,
                c.phone AS phone,
                o.date, 
                o.product,
                p.note AS product_note,
                COALESCE(o.price * 1.14, 0) AS price, 
                o.quantity AS weight, 
                w.quantity AS delivered
            FROM
                salmon_orders o
            LEFT JOIN 
                salmon_order_weight w ON o.id = w.order_id
            LEFT JOIN 
                salmon_customer c ON o.customer = c.customer
            LEFT JOIN
                salmon_product_name p ON o.product = p.product_name
            WHERE
                o.id = :order_id;
        """)
    try:
        result = session.execute(query, {'order_id': order_id})
        
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        df['expiry_date_fresh'] = df['date'] + pd.Timedelta(days=6)
        df['expiry_date_frozen'] = df['date'] + pd.Timedelta(days=90)

        df['date'] = pd.to_datetime(df['date'])
        df['expiry_date_fresh'] = pd.to_datetime(df['expiry_date_fresh'])
        df['expiry_date_frozen'] = pd.to_datetime(df['expiry_date_frozen'])

        df['date_z'] = df['date'].dt.strftime("%Y.%m.%d")
        df['date'] = df['date'].dt.strftime("%Y.%m.%d, %a")
        
        df['expiry_date_z_fresh'] = df['expiry_date_fresh'].dt.strftime("%Y.%m.%d")
        df['expiry_date_fresh'] = df['expiry_date_fresh'].dt.strftime("%Y.%m.%d, %a")

        df['expiry_date_z_frozen'] = df['expiry_date_frozen'].dt.strftime("%Y.%m.%d")
        df['expiry_date_frozen'] = df['expiry_date_frozen'].dt.strftime("%Y.%m.%d, %a")

        delivery_note_data = {}
        for column in df.columns:
            if column == 'delivered' and len(df)>1:
                delivery_note_data[column] = round(df[column].sum(),2)
            else:
                delivery_note_data[column] = df[column].iloc[0]
        if file_type =="pdf":
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('app/templates/salmon_delivery_template.html')
            rendered_html = template.render(delivery_note_data)
            hti = Html2Image(
                size=(2142, 3000),
                # custom_flags=['--no-sandbox', '--headless', '--disable-gpu', '--disable-software-rasterizer', '--disable-dev-shm-usage'],
                output_path=folder_path
                )
            # hti.browser_executable = "chromedriver.exe"
            random_hash = generate_random_hash()
            image_name = f'{random_hash}.png'
            image_path = f'{folder_path}/{image_name}'
            hti.screenshot(
                html_str=rendered_html,
                save_as=image_name,
                )
            images_to_pdf(image_path, output_dir='temp', repetition=2)
            if os.path.isfile(os.path.join(folder_path, f"{random_hash}.pdf")):
                print_document(os.path.join(folder_path, f"{random_hash}.pdf"))

                pass
        elif file_type =="zpl":
            zebra_print_list = zebra_generator(df)
            for i in zebra_print_list:
                print_zebra(zpl_data=i)
        else:
            print(f"Print failed due to unable to generate file.")

    except Exception as e:
        # If there's any error, rollback the session
        session.rollback()
        print(f"Error executing query: {e}")

    finally:
        # Close the session properly
        session.close()
    return df

def zebra_generator(df):
    zpl_template_x99_y63 = """
    ; Start of label
    ^XA

    ; Set UTF-8 Character Encoding
    ^CI28

    ; Draw the producer identifier
    ^FO270,40^GFA,1387,1387,19,,::::::::::S03MFC,:Q01FFM0FF8,P01F8O01F8,P0FCQ03F,O07CS03E,N07CU01F,M03CW01C,M0FM01F2O07,L018M0102O01C,L07N0102P06,K018N0102P018,K06O01F2Q06,K0EO01F2Q03,J018O0102Q018,J03P0102R0C,J06P0102R02,J0CP0102R01,I018gK018,I03gM0C,:I06gM06,I04gM02,I04O03018783CP03,I04O070188C46P03,I04O0502804C6P03,I04O010480I4P03,I04O010880838P03,I04O01188183CP03,I04O0110830C6P03,I04O011FC6082P02,I02O01008C0C6P06,I03O07C08FC7CP0C,I018gL08,I018gK018,J0CgK01,J06gK06,J03P07E84Q0C,J01CO04084P018,K0EO04084P03,K03O04048P0E,K01CN07878O038,L038M0403P0C,M0CM0403O038,M078L0403O0E,M01CL0403N078,N03EK07C3M07E,O03FS07E,P03EQ07E,Q07FO0FE,R07FEK03FE,T07KFE,,:::::::::^FS

    ; Add Producer info
    ^FO30,50^A0N,20,20^FDValmistaja / Tillverkare^FS
    ^FO30,75^A0N,25,25^FDSpartao Oy^FS
    ^FO30,110^A0N,20,20^FDY-tunnus: 2938534-6^FS
    ^FO30,130^A0N,20,20^FDOsoite: Nihtisillantie 3B, 02630 Espoo^FS
    ^FO30,150^A0N,20,20^FDPuh: +358 45 7831 9456^FS

    ; Add the Batch number
    ^FO470,50^A0N,20,20^FDEränumero / Batchnummer^FS
    ^FO470,75^A0N,25,25^FD{batch_number}^FS


    ; Add Product origin country
    ^FO470,115^A0N,20,20^FDAlkuperämaa / Ursprungslandet^FS
    ^FO470,140^A0N,30,30^FDNorja / Norge^FS

    ; Draw a line separator
    ^FO30,180^GB730,2,2^FS

    ; Add Product name
    ^FO30,195^A0N,20,20^FDAinesosat / Ingredienser^FS
    ^FO30,220^A0N,30,30^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    ; Add Product treatment
    ^FO540,195^A0N,20,20^FDTuote / Produkt^FS
    ^FO540,220^A0N,30,30^FD{product}^FS

    ; Add Product note
    ^FO30,265^A0N,25,35^FDNOTE: {product_note}^FS

    ; Add temperature
    ^FO30,305^A0N,20,20^FDSäilytys/ Förvaring^FS
    ^FO30,350^A0N,30,30^FD{temperature_info}^FS

    ; Add an Expiration date
    ^FO240,305^A0N,20,20^FDViimeinen käyttöpäivä^FS
    ^FO240,325^A0N,20,20^FD/ Sista förbrukningsdag^FS
    ^FO240,350^A0N,20,20^FD{expiry_info}^FS

    ; Add net weight
    ^FO540,305^A0N,20,20^FDNettopaino / Nettovikt^FS
    ^FO540,350^A0N,30,30^FD{delivered} KG^FS

    ; Draw a line separator
    ^FO30,400^GB730,2,2^FS

    ; Add order id
    ^FO30,415^A0N,20,20^FDTilausnumero^FS
    ^FO30,440^A0N,30,35^FD{order_id}^FS

    ; Add recipient
    ^FO240,415^A0N,20,20^FDAsiakas / Kund^FS
    ^FO240,440^A0N,30,40^FD{store}^FS

    ; End of label
    ^XZ
    """

    zpl_template_x55_y70 = """
    ; Start of label
    ^XA

    ^FO310,200^GFA,1750,1750,14,,:::::::::::::::P0IF,O07001C,N018I03,N02K0C,N0CK02,M018K01,M02M08,M04M06,M08M02,L01N01,L03O08,L02O04,L04O06,L08O02,L08O01,K01P01,K03Q08,K02Q0C,K06Q04,K04Q04,K0CQ02,K08Q02,K08Q01,J01R01,:J01S08,J02S08,:J02S04,:J04S04,J04L04L04,J04L02L02,J04J03FFL02,J08S02,::J087FCP02,J08C66004,J08842005M01,J08842I08L01,J08842I0400FFC01,J0884200C3I04401,J0884203FDI04401,J08802M04401,I01Q04401,:I01I060386J0401,J080180241L01,J080300241L01,J08FC0022100FFC01,J080400211L01,J08030021EL01,J0800CP01,J08006,J08J01EEL02,J08J0239L02,J08J0211L02,J04J0211L02,:J04J01EE,J04S04,:J02S04,:J02S08,J01S08,:J01R01,K08Q01,K08Q02,:K04Q02,K04Q04,K02Q04,K02Q08,K01Q08,K01P01,L08O03,L04O02,L04O04,L02O08,L01N018,M08M01,M0CM02,M06M04,M03L018,N08K03,N06K06,N03J018,O0EI06,O03C078,P03F8,,:::::::::::::::^FS


    ; Set UTF-8 Character Encoding
    ^CI28

    ; Add Producer info
    ^FO380,40^A0R,12,12^FDValmistaja / Tillverkare^FS
    ^FO350,40^A0R,15,15^FDSpartao Oy^FS
    ^FO330,40^A0R,12,12^FDY-tunnus: 2938534-6^FS
    ^FO310,40^A0R,12,12^FDOsoite: Nihtisillantie 3B, 02630 Espoo^FS
    ^FO290,40^A0R,12,12^FDPuh: +358 45 7831 9456^FS

    ; Add the Batch number
    ^FO380,350^A0R,12,12^FDEränumero / Batchnummer^FS
    ^FO350,350^A0R,15,15^FD{batch_number}^FS

    ; Add Product origin country
    ^FO310,350^A0R,12,12^FDAlkuperämaa / Ursprungslandet^FS
    ^FO290,350^A0R,15,15^FDNorja / Norge^FS

    ; Add Product name
    ^FO250,40^A0R,12,12^FDAinesosat / Ingredienser^FS
    ^FO230,40^A0R,15,15^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS
    ; Add Product note
    ^FO210,40^A0R,15,15^FDNOTE: {product_note}^FS


    ; Add Product treatment
    ^FO250,350^A0R,12,12^FDTuote / Produkt^FS
    ^FO220,350^A0R,25,25^FD{product}^FS


    ; Add temperature
    ^FO170,40^A0R,12,12^FDSäilytys/ Förvaring^FS
    ^FO130,40^A0R,20,20^FD{temperature_info}^FS

    ; Add an Expiration date
    ^FO170,200^A0R,12,12^FDViimeinen käyttöpäivä^FS
    ^FO155,200^A0R,12,12^FD/ Sista förbrukningsdag^FS
    ^FO130,200^A0R,20,15^FD{expiry_info}^FS

    ; Add net weight
    ^FO170,400^A0R,12,12^FDNettopaino / Nettovikt^FS
    ^FO130,400^A0R,20,20^FD{delivered} KG^FS


    ; Add order id
    ^FO90,40^A0R,12,12^FDTilausnumero^FS
    ^FO60,40^A0R,20,25^FD{order_id}^FS

    ; Add recipient
    ^FO90,200^A0R,12,12^FDAsiakas / Kund^FS
    ^FO60,200^A0R,20,25^FD{store}^FS

    ; End of label
    ^XZ
    """
    
    zpl_labels = []
    for _, row in df.iterrows():
        if 'Frozen' in row['product']:
            temperature_info = "-18°C"
            expiry_info = f"{row['expiry_date_z_frozen']}"
            product_name = f"{row['product'].replace('Lohi ','')}"
        elif 'Frozen' not in row['product']:
            temperature_info = "0°C - +2°C"
            expiry_info = f"{row['date_z']}-{row['expiry_date_z_fresh']}"
            product_name = f"{row['product']}"


        zpl_label = zpl_template_x55_y70.format(
            order_id=row['order_id'],
            store=row['store'],
            product=product_name,
            product_note=row['product_note'],
            delivered=row['delivered'],
            temperature_info=temperature_info,
            expiry_info=expiry_info,
            batch_number=row['date_z'].replace(".",""),
        )
        zpl_labels.append(zpl_label)
    return zpl_labels
