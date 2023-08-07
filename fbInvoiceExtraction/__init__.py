import os
import logging
import tempfile
from pdf2image import convert_from_path, convert_from_bytes
import cv2
import pytesseract
import json
import base64
import numpy as np
from azure.functions import HttpRequest, HttpResponse
from pytesseract import Output

'''
Adding to check version number in Azure: 
V1.0.3
'''

locs = [{'account_no': {'left': 304, 'top': 341, 'width':75, 'height': 18}},
        {'po_no':{'left': 381, 'top': 401, 'width':106, 'height': 18}},
        {'reference_document': {'left': 664, 'top': 986, 'width':136, 'height': 30}},
        {'document_no':{'left': 2091, 'top': 201, 'width':179, 'height': 38}},
        {'document_type':{'left': 2091, 'top': 261, 'width':179, 'height': 38}},
        {'invoice_date':{'left': 2091, 'top': 321, 'width':179, 'height': 38}},
        {'net_total':{'left': 1889, 'top': 1019, 'width':126, 'height': 38}},
        {'total_vat':{'left': 2017, 'top': 1019, 'width':126, 'height': 38}},
        {'gross_total':{'left': 2145, 'top': 1019, 'width':126, 'height': 38}}]


# Function to accept the PDF content and return array of pages
def create_temp_dir(pdf_bytes):    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save PDF to a temporary file
        pdf_path = os.path.join(temp_dir, 'input.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        images = convert_from_path(pdf_path)
    return images    

def extract_text_from_images(roi_image):
    # Convert the image to grayscale explicitly
    # roi_gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
    # roi = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    roi = roi_image
    d = pytesseract.image_to_data(roi, output_type=Output.DICT, config='--psm 6')
    if 'text' in d and len(d['text']) >= 5:
        return d['text'][4]  # Return the 5th element of the 'text' list
    else:
        return None

def process_images(images, locs):
    results = {}
    for PIL_Image in images:
        pdf_image = np.array(PIL_Image)
        result = pdf_image.copy()
        gray = cv2.cvtColor(pdf_image, cv2.COLOR_RGB2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80,1))
        rem_hor = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hor_kernel, iterations=2)
        cnts = cv2.findContours(rem_hor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(result, [c], -1, (255, 255, 255), 3)

        ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,80))
        rem_ver = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, ver_kernel, iterations=2)
        cnts = cv2.findContours(rem_ver, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(result, [c], -1, (255, 255, 255), 4)

        mask = np.all(result == [178,178,178], axis=-1)
        result[mask] = [255,255,255]
        threshed = result

        for item in locs:
            key = next(iter(item))
            x, y, w, h = item[key]['left'], item[key]['top'], item[key]['width'], item[key]['height']
            roi = threshed[y:y+h, x:x+w]
            text = extract_text_from_images(roi)
            results[key] = text
    return results

def main(req: HttpRequest) -> HttpResponse:
    try:
        logging.info("Received a request.")

        req_body = req.get_body()
        pdf_content = base64.b64decode(req_body) 
 
        logging.debug("Decoded PDF content.")

        images = convert_from_bytes(pdf_content)
        
        logging.debug("Successfully extracted images.")

        extracted_text = process_images(images, locs)
        
        logging.debug("Processed images and extracted text.")

        headers = {'Content-Type': 'application/json'}
        return HttpResponse(json.dumps(extracted_text), headers=headers)

    except Exception as e:
        logging.error("Error occurred: %s", str(e))
        return HttpResponse(f"Error occurred: {str(e)}", status_code=500)


