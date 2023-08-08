import os
import logging
import tempfile
from pdf2image import convert_from_bytes
import cv2
import pytesseract
import json
import base64
import numpy as np
from azure.functions import HttpRequest, HttpResponse
from pytesseract import Output

# List containing dictionary for each region of interest for extraction 
# [{'label': {'pixel locations'}]
locs = [{'account_no': {'left': 304, 'top': 341, 'width':75, 'height': 18}},
        {'po_no':{'left': 381, 'top': 401, 'width':106, 'height': 18}},
        {'reference_document': {'left': 664, 'top': 986, 'width':136, 'height': 30}},
        {'document_no':{'left': 2091, 'top': 201, 'width':179, 'height': 38}},
        {'document_type':{'left': 2091, 'top': 261, 'width':179, 'height': 38}},
        {'invoice_date':{'left': 2091, 'top': 321, 'width':179, 'height': 38}},
        {'net_total':{'left': 1889, 'top': 1019, 'width':126, 'height': 38}},
        {'total_vat':{'left': 2017, 'top': 1019, 'width':126, 'height': 38}},
        {'gross_total':{'left': 2145, 'top': 1019, 'width':126, 'height': 38}}]

def extract_text_from_images(roi_image):
    """
    Extracts text from a region of interest (ROI) image.
    Args:
        roi_image: Binary image data containing the region of interest.
    Returns:
        Extracted text from the ROI image.
    """    
    roi = roi_image
    d = pytesseract.image_to_data(roi, output_type=Output.DICT, config='--psm 6')
    if 'text' in d and len(d['text']) >= 5:
        return d['text'][4]  # Return the 5th element of the 'text' list
    else:
        return None

def process_images(images, locs):
    """
    Processes a list of images and extracts text from specified regions of interest.
    Args:
        images: List of PIL images to be processed.
        locs: List of dictionaries containing pixel locations for ROIs.
    Returns:
        A dictionary containing extracted text for each specified label.
    """
    results = {}
    for PIL_Image in images:
        pdf_image = np.array(PIL_Image)
        result = pdf_image.copy()
        
        # Convert the image to grayscale
        gray = cv2.cvtColor(pdf_image, cv2.COLOR_RGB2GRAY)
        
        # Apply Otsu's thresholding to obtain binary image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Perform horizontal line removal using morphological operations
        hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (80, 1))
        rem_hor = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hor_kernel, iterations=2)
        
        # Find and draw contours around horizontal lines
        cnts = cv2.findContours(rem_hor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(result, [c], -1, (255, 255, 255), 3)

        # Perform vertical line removal using morphological operations
        ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 80))
        rem_ver = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, ver_kernel, iterations=2)
        
        # Find and draw contours around vertical lines
        cnts = cv2.findContours(rem_ver, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            cv2.drawContours(result, [c], -1, (255, 255, 255), 4)

        # Create a mask to identify specific color values and replace them
        # with white. This removes the grey background of certain cells.
        mask = np.all(result == [178, 178, 178], axis=-1)
        result[mask] = [255, 255, 255]
        threshed = result

        # Extract text from each region of interest (ROI)
        for item in locs:
            key = next(iter(item))
            x, y, w, h = item[key]['left'], item[key]['top'], item[key]['width'], item[key]['height']
            
            # Crop the image to the specified ROI
            roi = threshed[y:y+h, x:x+w]
            
            # Extract text from the cropped ROI
            text = extract_text_from_images(roi)
            results[key] = text
    return results

def main(req: HttpRequest) -> HttpResponse:
    try:
        logging.info("Received a request.")

        # Get the request body containing PDF content
        req_body = req.get_body()
        pdf_content = base64.b64decode(req_body) 
 
        logging.debug("Decoded PDF content.")

        # Convert the PDF content into a list of PIL images
        images = convert_from_bytes(pdf_content)
        
        logging.debug("Successfully extracted images.")

        # Process the extracted images and extract text from specified regions
        extracted_text = process_images(images, locs)
        
        logging.debug("Processed images and extracted text.")

        # Prepare the response with extracted text in JSON format
        headers = {'Content-Type': 'application/json'}
        return HttpResponse(json.dumps(extracted_text), headers=headers)

    except Exception as e:
        logging.error("Error occurred: %s", str(e))
        return HttpResponse(f"Error occurred: {str(e)}", status_code=500)

#Copyright 2023 Ethan Davies
