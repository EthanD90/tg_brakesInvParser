FROM mcr.microsoft.com/azure-functions/python:3.0-python3.9
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils
COPY requirements.txt /
RUN pip install -r /requirements.txt
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
COPY . /home/site/wwwroot
