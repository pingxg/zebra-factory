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



def pdf_render_print(order_id, file_type, folder_path="temp"):
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
                p.display_name AS product,
                p.note AS product_note,
                COALESCE(o.price * 1.14, 0) AS price, 
                o.quantity AS weight, 
                w.quantity AS delivered,
                c.priority,
                COUNT(*) OVER () AS box_count,
                c.hide_company_name
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
        df['expiry_date_frozen'] = df['date'] + pd.Timedelta(days=180)

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

        if file_type =="zpl":
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
    # zpl_template_x99_y63 = """
    # ; Start of label
    # ^XA

    # ; Set UTF-8 Character Encoding
    # ^CI28

    # ; Draw the producer identifier
    # ^FO200,50^GFA,1387,1387,19,,::::::::::S03MFC,:Q01FFM0FF8,P01F8O01F8,P0FCQ03F,O07CS03E,N07CU01F,M03CW01C,M0FM01F2O07,L018M0102O01C,L07N0102P06,K018N0102P018,K06O01F2Q06,K0EO01F2Q03,J018O0102Q018,J03P0102R0C,J06P0102R02,J0CP0102R01,I018gK018,I03gM0C,:I06gM06,I04gM02,I04O03018783CP03,I04O070188C46P03,I04O0502804C6P03,I04O010480I4P03,I04O010880838P03,I04O01188183CP03,I04O0110830C6P03,I04O011FC6082P02,I02O01008C0C6P06,I03O07C08FC7CP0C,I018gL08,I018gK018,J0CgK01,J06gK06,J03P07E84Q0C,J01CO04084P018,K0EO04084P03,K03O04048P0E,K01CN07878O038,L038M0403P0C,M0CM0403O038,M078L0403O0E,M01CL0403N078,N03EK07C3M07E,O03FS07E,P03EQ07E,Q07FO0FE,R07FEK03FE,T07KFE,,:::::::::^FS

    # ; Add Producer info
    # ^FO30,50^A0N,20,20^FDValmistaja / Tillverkare^FS
    # ^FO30,75^A0N,25,25^FDSpartao Oy^FS
    # ^FO30,110^A0N,20,20^FDY-tunnus: 2938534-6^FS
    # ^FO30,130^A0N,20,20^FDOsoite: Nihtisillantie 3B, 02630 Espoo^FS
    # ^FO30,150^A0N,20,20^FDPuh: +358 45 7831 9456^FS

    # ; Add the Batch number
    # ^FO350,50^A0N,20,20^FDEränumero / Batchnummer^FS
    # ^FO350,75^A0N,25,25^FD{batch_number}^FS


    # ; Add Product origin country
    # ^FO350,115^A0N,20,20^FDAlkuperämaa / Ursprungslandet^FS
    # ^FO350,140^A0N,30,30^FDNorja / Norge^FS


    # ; Add Priority
    # ^FO600,50^A0N,20,20^FDEtusijalla / Prioritet^FS
    # ^FO700,85^A0N,90,90^FD{priority}^FS

    # ; Draw a line separator
    # ^FO30,180^GB730,2,2^FS

    # ; Add Product name
    # ^FO30,195^A0N,20,20^FDAinesosat / Ingredienser^FS
    # ^FO30,220^A0N,30,30^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    # ; Add Product treatment
    # ^FO540,195^A0N,20,20^FDTuote / Produkt^FS
    # ^FO540,220^A0N,30,30^FD{product}^FS

    # ; Add Product note
    # ^FO30,265^A0N,25,35^FDNOTE: {product_note}^FS

    # ; Add temperature
    # ^FO30,305^A0N,20,20^FDSäilytys/ Förvaring^FS
    # ^FO30,350^A0N,30,30^FD{temperature_info}^FS

    # ; Add an Expiration date
    # ^FO240,305^A0N,20,20^FDViimeinen käyttöpäivä^FS
    # ^FO240,325^A0N,20,20^FD/ Sista förbrukningsdag^FS
    # ^FO240,350^A0N,20,20^FD{expiry_info}^FS

    # ; Add net weight
    # ^FO540,305^A0N,20,20^FDNettopaino / Nettovikt^FS
    # ^FO540,350^A0N,30,30^FD{delivered} KG^FS

    # ; Draw a line separator
    # ^FO30,400^GB730,2,2^FS

    # ; Add order id
    # ^FO30,415^A0N,20,20^FDTilausnumero^FS
    # ^FO30,440^A0N,30,25^FD{order_id}^FS

    # ; Add recipient
    # ^FO160,415^A0N,20,20^FDAsiakas / Kund^FS
    # ^FO160,440^A0N,30,40^FD{store}^FS

    # ; Add box count
    # ^FO490,415^A0N,20,20^FDLaatikoita yhteensä / Totala lådor^FS
    # ^FO650,440^A0N,35,35^FD{box_count} CTN^FS

    # ; End of label
    # ^XZ
    # """

    # zpl_template_x55_y70 = """
    # ; Start of label
    # ^XA

    # ^FO335,160^GFA,1750,1750,14,,:::::::::::::::P0IF,O07001C,N018I03,N02K0C,N0CK02,M018K01,M02M08,M04M06,M08M02,L01N01,L03O08,L02O04,L04O06,L08O02,L08O01,K01P01,K03Q08,K02Q0C,K06Q04,K04Q04,K0CQ02,K08Q02,K08Q01,J01R01,:J01S08,J02S08,:J02S04,:J04S04,J04L04L04,J04L02L02,J04J03FFL02,J08S02,::J087FCP02,J08C66004,J08842005M01,J08842I08L01,J08842I0400FFC01,J0884200C3I04401,J0884203FDI04401,J08802M04401,I01Q04401,:I01I060386J0401,J080180241L01,J080300241L01,J08FC0022100FFC01,J080400211L01,J08030021EL01,J0800CP01,J08006,J08J01EEL02,J08J0239L02,J08J0211L02,J04J0211L02,:J04J01EE,J04S04,:J02S04,:J02S08,J01S08,:J01R01,K08Q01,K08Q02,:K04Q02,K04Q04,K02Q04,K02Q08,K01Q08,K01P01,L08O03,L04O02,L04O04,L02O08,L01N018,M08M01,M0CM02,M06M04,M03L018,N08K03,N06K06,N03J018,O0EI06,O03C078,P03F8,,:::::::::::::::^FS


    # ; Set UTF-8 Character Encoding
    # ^CI28

    # ; Add Producer info
    # ^FO390,30^A0R,15,15^FDValmistaja / Tillverkare^FS
    # ^FO360,30^A0R,25,25^FDSpartao Oy^FS
    # ^FO340,30^A0R,15,15^FD2938534-6^FS
    # ^FO325,30^A0R,15,15^FDNihtisillantie 3B, 02630 Espoo^FS
    # ^FO310,30^A0R,15,15^FD045 7831 9456^FS

    # ; Add the Batch number
    # ^FO390,275^A0R,15,13^FDEränumero / Batchnummer^FS
    # ^FO370,275^A0R,20,20^FD{batch_number}^FS

    # ; Add Priority
    # ^FO390,445^A0R,15,12^FDEtusijalla / Prioritet^FS
    # ^FO280,460^A0R,80,80^FD{priority}^FS


    # ; Add Product origin country
    # ^FO340,275^A0R,15,12^FDAlkuperämaa / Ursprungslandet^FS
    # ^FO315,275^A0R,20,20^FDNorja / Norge^FS

    # ; Add Product name
    # ^FO270,30^A0R,15,15^FDAinesosat / Ingredienser^FS
    # ^FO240,30^A0R,20,20^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    # ; Add Product treatment
    # ^FO270,360^A0R,15,15^FDTuote / Produkt^FS
    # ^FO240,360^A0R,25,25^FD{product}^FS

    # ; Add temperature
    # ^FO170,30^A0R,15,15^FDSäilytys/ Förvaring^FS
    # ^FO120,30^A0R,20,20^FD{temperature_info}^FS

    # ; Add an Expiration date
    # ^FO170,200^A0R,15,15^FDViimeinen käyttöpäivä^FS
    # ^FO150,200^A0R,15,15^FD/ Sista förbrukningsdag^FS
    # ^FO120,200^A0R,20,20^FD{expiry_info}^FS

    # ; Add net weight
    # ^FO170,400^A0R,15,15^FDNettopaino / Nettovikt^FS
    # ^FO120,440^A0R,25,25^FD{delivered} KG^FS

    # ; Add order id
    # ^FO70,30^A0R,15,15^FDTilausnumero^FS
    # ^FO40,30^A0R,20,18^FD{order_id}^FS

    # ; Add recipient
    # ^FO70,140^A0R,15,15^FDAsiakas / Kund^FS
    # ^FO30,140^A0R,35,25^FD{store}^FS

    # ; Add box count
    # ^FO70,330^A0R,15,15^FDLaatikoita yhteensä / Totala lådor^FS
    # ^FO30,460^A0R,30,30^FD{box_count} CTN^FS


    # ; End of label
    # ^XZ
    # """

    # zpl_template_x76_y102 = """
    # ; Start of label
    # ^XA

    # ^FO450,210^GFA,1750,1750,14,,:::::::::::::::P0IF,O07001C,N018I03,N02K0C,N0CK02,M018K01,M02M08,M04M06,M08M02,L01N01,L03O08,L02O04,L04O06,L08O02,L08O01,K01P01,K03Q08,K02Q0C,K06Q04,K04Q04,K0CQ02,K08Q02,K08Q01,J01R01,:J01S08,J02S08,:J02S04,:J04S04,J04L04L04,J04L02L02,J04J03FFL02,J08S02,::J087FCP02,J08C66004,J08842005M01,J08842I08L01,J08842I0400FFC01,J0884200C3I04401,J0884203FDI04401,J08802M04401,I01Q04401,:I01I060386J0401,J080180241L01,J080300241L01,J08FC0022100FFC01,J080400211L01,J08030021EL01,J0800CP01,J08006,J08J01EEL02,J08J0239L02,J08J0211L02,J04J0211L02,:J04J01EE,J04S04,:J02S04,:J02S08,J01S08,:J01R01,K08Q01,K08Q02,:K04Q02,K04Q04,K02Q04,K02Q08,K01Q08,K01P01,L08O03,L04O02,L04O04,L02O08,L01N018,M08M01,M0CM02,M06M04,M03L018,N08K03,N06K06,N03J018,O0EI06,O03C078,P03F8,,:::::::::::::::^FS

    # ; Set UTF-8 Character Encoding
    # ^CI28

    # ; Add Producer info
    # ^FO500,40^A0R,20,20^FDValmistaja / Tillverkare^FS
    # ^FO460,40^A0R,30,30^FDSpartao Oy^FS
    # ^FO430,40^A0R,20,20^FD2938534-6^FS
    # ^FO400,40^A0R,20,20^FDNihtisillantie 3B, 02630 Espoo^FS
    # ^FO370,40^A0R,20,20^FD045 7831 9456^FS

    # ; Add the Batch number
    # ^FO500,350^A0R,20,18^FDEränumero / Batchnummer^FS
    # ^FO470,350^A0R,25,25^FD{batch_number}^FS

    # ; Add Priority
    # ^FO500,560^A0R,20,18^FDEtusijalla / Prioritet^FS
    # ^FO360,580^A0R,100,100^FD{priority}^FS

    # ; Add Product origin country
    # ^FO430,350^A0R,20,18^FDAlkuperämaa / Ursprungslandet^FS
    # ^FO390,350^A0R,25,25^FDNorja / Norge^FS

    # ; Add Product name
    # ^FO330,40^A0R,20,20^FDAinesosat / Ingredienser^FS
    # ^FO290,40^A0R,25,25^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    # ; Add Product treatment
    # ^FO330,470^A0R,20,20^FDTuote / Produkt^FS
    # ^FO290,470^A0R,30,25^FD{product}^FS

    # ; Add temperature
    # ^FO230,40^A0R,20,20^FDSäilytys / Förvaring^FS
    # ^FO170,40^A0R,25,25^FD{temperature_info}^FS

    # ; Add an Expiration date
    # ^FO230,260^A0R,20,20^FDViimeinen käyttöpäivä^FS
    # ^FO200,260^A0R,20,20^FD/ Sista förbrukningsdag^FS
    # ^FO170,260^A0R,25,25^FD{expiry_info}^FS

    # ; Add net weight
    # ^FO230,520^A0R,20,20^FDNettopaino / Nettovikt^FS
    # ^FO170,570^A0R,35,35^FD{delivered} KG^FS

    # ; Add order ID
    # ^FO100,40^A0R,20,20^FDTilausnumero^FS
    # ^FO60,40^A0R,25,25^FD{order_id}^FS

    # ; Add recipient
    # ^FO100,180^A0R,20,20^FDAsiakas / Kund^FS
    # ^FO50,180^A0R,40,35^FD{store}^FS

    # ; Add box count
    # ^FO100,430^A0R,20,20^FDLaatikoita yhteensä / Totala lådor^FS
    # ^FO50,600^A0R,40,40^FD{box_count} CTN^FS

    # ; End of label
    # ^XZ
    # """

    # zpl_template_x76_y102_bp = """
    # ; Start of label
    # ^XA

    # ^FO450,210^GFA,1750,1750,14,,:::::::::::::::P0IF,O07001C,N018I03,N02K0C,N0CK02,M018K01,M02M08,M04M06,M08M02,L01N01,L03O08,L02O04,L04O06,L08O02,L08O01,K01P01,K03Q08,K02Q0C,K06Q04,K04Q04,K0CQ02,K08Q02,K08Q01,J01R01,:J01S08,J02S08,:J02S04,:J04S04,J04L04L04,J04L02L02,J04J03FFL02,J08S02,::J087FCP02,J08C66004,J08842005M01,J08842I08L01,J08842I0400FFC01,J0884200C3I04401,J0884203FDI04401,J08802M04401,I01Q04401,:I01I060386J0401,J080180241L01,J080300241L01,J08FC0022100FFC01,J080400211L01,J08030021EL01,J0800CP01,J08006,J08J01EEL02,J08J0239L02,J08J0211L02,J04J0211L02,:J04J01EE,J04S04,:J02S04,:J02S08,J01S08,:J01R01,K08Q01,K08Q02,:K04Q02,K04Q04,K02Q04,K02Q08,K01Q08,K01P01,L08O03,L04O02,L04O04,L02O08,L01N018,M08M01,M0CM02,M06M04,M03L018,N08K03,N06K06,N03J018,O0EI06,O03C078,P03F8,,:::::::::::::::^FS

    # ; Set UTF-8 Character Encoding
    # ^CI28

    # ; Add Producer info
    # ^FO500,40^A0R,20,20^FDValmistaja / Tillverkare^FS
    # ^FO460,40^A0R,30,30^FDSpartao Oy^FS
    # ^FO430,40^A0R,20,20^FD2938534-6^FS
    # ^FO400,40^A0R,20,20^FDNihtisillantie 3B, 02630 Espoo^FS
    # ^FO370,40^A0R,20,20^FD045 7831 9456^FS

    # ; Add the Batch number
    # ^FO500,350^A0R,20,18^FDEränumero / Batchnummer^FS
    # ^FO470,350^A0R,25,25^FD{batch_number}^FS

    # ; Add Product origin country
    # ^FO430,350^A0R,20,18^FDAlkuperämaa / Ursprungslandet^FS
    # ^FO390,350^A0R,25,25^FDNorja / Norge^FS

    # ; Add Product name
    # ^FO330,40^A0R,20,20^FDAinesosat / Ingredienser^FS
    # ^FO290,40^A0R,25,25^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    # ; Add Product treatment
    # ^FO330,470^A0R,20,20^FDTuote / Produkt^FS
    # ^FO290,470^A0R,30,25^FD{product}^FS

    # ; Add temperature
    # ^FO230,40^A0R,20,20^FDSäilytys / Förvaring^FS
    # ^FO170,40^A0R,25,25^FD{temperature_info}^FS

    # ; Add an Expiration date
    # ^FO230,260^A0R,20,20^FDViimeinen käyttöpäivä^FS
    # ^FO200,260^A0R,20,20^FD/ Sista förbrukningsdag^FS
    # ^FO170,260^A0R,25,25^FD{expiry_info}^FS

    # ; Add product type
    # ^FO100,40^A0R,25,25^FDLuokan 3 sivutuote / Klass 3 biprodukt^FS
    # ^FO50,40^A0R,30,30^FD3 luokan sivutuote, ei ihmisravinnoksi.^FS

    # ; End of label
    # ^XZ
    # """

    zpl_template_x110_y80 = """
    ^XA

    ; 设置 UTF-8 编码
    ^CI28

    ; 生产商标识图案（稍微上移）
    ^FO260,80^GFA,1387,1387,19,,::::::::::S03MFC,:Q01FFM0FF8,P01F8O01F8,P0FCQ03F,O07CS03E,N07CU01F,M03CW01C,M0FM01F2O07,L018M0102O01C,L07N0102P06,K018N0102P018,K06O01F2Q06,K0EO01F2Q03,J018O0102Q018,J03P0102R0C,J06P0102R02,J0CP0102R01,I018gK018,I03gM0C,:I06gM06,I04gM02,I04O03018783CP03,I04O070188C46P03,I04O0502804C6P03,I04O010480I4P03,I04O010880838P03,I04O01188183CP03,I04O0110830C6P03,I04O011FC6082P02,I02O01008C0C6P06,I03O07C08FC7CP0C,I018gL08,I018gK018,J0CgK01,J06gK06,J03P07E84Q0C,J01CO04084P018,K0EO04084P03,K03O04048P0E,K01CN07878O038,L038M0403P0C,M0CM0403O038,M078L0403O0E,M01CL0403N078,N03EK07C3M07E,O03FS07E,P03EQ07E,Q07FO0FE,R07FEK03FE,T07KFE,,:::::::::^FS

    ; **生产商信息（间距增大）**
    ^FO30,90^A0N,24,24^FDValmistaja / Tillverkare^FS
    ^FO30,120^A0N,30,30^FD{company_display}^FS
    ^FO30,160^A0N,24,24^FDY-tunnus: 2938534-6^FS
    ^FO30,190^A0N,24,24^FDOsoite: {company_address}^FS
    ^FO30,220^A0N,24,24^FDPuh: {company_phone}^FS

    ; **批次号**
    ^FO400,90^A0N,24,20^FDEränumero / Batchnummer^FS
    ^FO400,120^A0N,32,26^FD{batch_number}^FS

    ; **原产国**
    ^FO400,170^A0N,24,20^FDAlkuperämaa / Ursprungslandet^FS
    ^FO400,200^A0N,34,28^FDNorja / Norge^FS

    ; **优先级（字体加大）**
    ^FO680,90^A0N,24,20^FDEtusijalla / Prioritet^FS
    ^FO670,130^A0N,120,90^FD{priority}^FS

    ; **分隔线（加宽 + 下移）**
    ^FO30,250^GB850,2,2^FS

    ; **产品名称**
    ^FO30,270^A0N,24,24^FDAinesosat / Ingredienser^FS
    ^FO30,315^A0N,30,30^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    ; **处理方式**
    ^FO580,270^A0N,24,20^FDTuote / Produkt^FS
    ^FO580,310^A0N,36,28^FD{product}^FS

    ; **存储信息（间距增大）**
    ^FO30,370^A0N,24,24^FDSäilytys / Förvaring^FS
    ^FO30,430^A0N,30,30^FD{temperature_info}^FS

    ; **过期日期**
    ^FO280,370^A0N,24,20^FDViimeinen käyttöpäivä^FS
    ^FO280,400^A0N,24,20^FD/ Sista förbrukningsdag^FS
    ^FO280,430^A0N,32,26^FD{expiry_info}^FS

    ; **净重**
    ^FO580,370^A0N,24,20^FDNettopaino / Nettovikt^FS
    ^FO580,420^A0N,36,28^FD{delivered} KG^FS

    ; **分隔线**
    ^FO30,480^GB850,2,2^FS

    ; **订单编号**
    ^FO30,500^A0N,24,24^FDTilausnumero^FS
    ^FO30,540^A0N,36,36^FD{order_id}^FS

    ; **收货方**
    ^FO200,500^A0N,24,24^FDAsiakas / Kund^FS
    ^FO200,540^A0N,36,35^FD{store}^FS

    ; **盒数**
    ^FO540,500^A0N,24,24^FDLaatikoita yhteensä / Totala lådor^FS
    ^FO720,540^A0N,40,25^FD{box_count} CTN^FS

    ^XZ

    """

    zpl_template_x110_y80_bp = """
    ^XA

    ; 设置 UTF-8 编码
    ^CI28

    ; **生产商信息**
    ^FO30,40^A0N,26,26^FDValmistaja / Tillverkare^FS
    ^FO30,80^A0N,34,34^FD{company_display}^FS
    ^FO30,130^A0N,26,26^FDY-tunnus: 2938534-6^FS
    ^FO30,160^A0N,26,23^FDOsoite: Nihtisillantie 3B, 02630 Espoo^FS
    ^FO30,190^A0N,26,26^FDPuh: +358 45 7831 9456^FS

    ; **批次号**
    ^FO400,40^A0N,26,26^FDEränumero / Batchnummer^FS
    ^FO400,80^A0N,38,38^FD{batch_number}^FS

    ; **原产国**
    ^FO400,140^A0N,26,26^FDAlkuperämaa / Ursprungslandet^FS
    ^FO400,180^A0N,40,40^FDNorja / Norge^FS

    ; **分隔线**
    ^FO30,230^GB850,2,2^FS

    ; **产品名称**
    ^FO30,260^A0N,26,26^FDAinesosat / Ingredienser^FS
    ^FO30,310^A0N,30,30^FDViljelty LOHI / Odlad LAX (Salmo Salar)^FS

    ; **处理方式**
    ^FO580,260^A0N,26,26^FDTuote / Produkt^FS
    ^FO580,300^A0N,42,42^FD{product}^FS

    ; **存储信息**
    ^FO30,370^A0N,26,26^FDSäilytys / Förvaring^FS
    ^FO30,410^A0N,40,40^FD{temperature_info}^FS

    ; **过期日期**
    ^FO400,370^A0N,26,26^FDViimeinen käyttöpäivä^FS
    ^FO400,410^A0N,26,26^FD/ Sista förbrukningsdag^FS
    ^FO400,450^A0N,35,35^FD{expiry_info}^FS

    ; **产品类型**
    ^FO30,510^A0N,26,26^FDLuokan 3 sivutuote / Klass 3 biprodukt^FS
    ^FO30,550^A0N,42,42^FD3 luokan sivutuote, ei ihmisravinnoksi.^FS

    ^XZ

    """
    df['priority'] = df.apply(lambda row: "" if row['hide_company_name'] == 1 else row['priority'].split(' ')[1], axis=1)
    
    df['company_display'] = df['hide_company_name'].apply(lambda x: "" if x == 1 else "Spartao Oy")
    df['company_address'] = df['company_address'].apply(lambda x: "Maalarinkuja 2, 06150 Porvoo" if x == 1 else "Nihtisillantie 3B, 02630 Espoo")
    df['company_phone'] = df['company_phone'].apply(lambda x: "+358 319 521 9900" if x == 1 else "+358 45 7831 9456")
    zpl_labels = []
    for _, row in df.iterrows():
        if 'Frozen' in row['product']:
            temperature_info = "<-18°C"
            expiry_info = f"{row['expiry_date_z_frozen']}"
            product_name = f"{row['product'].replace('Lohi ','')}"
        elif 'Frozen' not in row['product']:
            temperature_info = "0°C - +2°C"
            expiry_info = f"{row['date_z']}-{row['expiry_date_z_fresh']}"
            product_name = f"{row['product']}"

        if row['product'] == "Frozen Lohi By-product":
            template = zpl_template_x110_y80_bp
        else:
            template = zpl_template_x110_y80
        zpl_label = template.format(
            order_id=row['order_id'],
            store=row['store'],
            product=product_name,
            product_note=row['product_note'],
            delivered=row['delivered'],
            temperature_info=temperature_info,
            expiry_info=expiry_info,
            batch_number=row['date_z'].replace(".",""),
            priority=row['priority'],
            box_count=row['box_count'],
            company_display=row['company_display'],
            company_address=row['company_address'],
            phone=row['company_phone']
        )
        zpl_labels.append(zpl_label)
    return zpl_labels
