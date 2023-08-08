# PDF Text Extraction with Image Processing

This repository contains code for extracting text from regions of interest (ROIs) in PDF documents using image processing techniques. The extracted text is then returned in JSON format.
The use case was to extract ROIs from invoices supplied by a single vendor, but can be adapted to suit other use cases.

Implementation assumes hosting as a Function in Azure Function Apps, for more details check out the documentation from Microsoft:
- [Azure Functions Overview](https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview?pivots=programming-language-python)

## Prerequisites

- Python 3.x
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- 
## Docker Installation + Usage

```bash
#Step 1 - Download the image from Docker Hub
docker pull edav90/ocrfunctionsimage:V1.0.0

#Step 2 - Run the image
docker run -p 8080:80 edav90/ocrfunctionsimage:V1.0.0
```
You can then try making a POST request to __init__.py at **http://localhost:8080/api/__init__**

## Traditional Installation + Usage

1. Clone this repository to your local machine:

```bash
git clone https://github.com/EthanD90/tg_brakesInvParser
cd tg_brakesInvParser
```
2. Install required python packages

```bash pip install -r requirements.txt```

3. Run the Azure Function locally:

```bash func start ```

*Note that this must be run in a virtual environment*

For more information and guidance on running Azure Functions locally, check the [Azure Resources](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Cportal%2Cv2%2Cbash&pivots=programming-language-python)

## Configuration
- Modify the locs list in the **__init__.py** file to define the regions of interest (ROIs) and their pixel locations.
- Adjust image processing parameters in the **__init__.py** file **process_images** function as needed.
- Configure logging levels and outputs in the host.json file.

## License

This project is licensed under the **GNU GPLv3 License**
