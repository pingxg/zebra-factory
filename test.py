import streamlit as st
import cv2
from pytesseract import image_to_string
from pytesseract import pytesseract

pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if it's different on your system

import streamlit as st
import cv2
import pytesseract
from PIL import Image
import numpy as np

def extract_numbers_from_image(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Use Tesseract to extract text from the image
    text = pytesseract.image_to_string(gray, config='--psm 6')
    
    # Extract numbers from the detected text
    numbers = ''.join(filter(str.isdigit, text))
    
    return numbers

st.title('Image Number Extractor')

captured_image = st.camera_input("test")


if captured_image:
    st.image(captured_image, caption="Captured Image", use_column_width=True)
    
    # Convert Streamlit's image to PIL format
    pil_image = Image.open(captured_image).convert("RGB")
    
    # Convert PIL image to numpy array
    np_image = np.array(pil_image)
    
    # Convert numpy array to OpenCV format
    opencv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
    
    numbers = extract_numbers_from_image(opencv_image)
    st.write(f"Extracted Numbers: {numbers}")