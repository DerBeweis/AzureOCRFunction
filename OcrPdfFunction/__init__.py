import logging
import azure.functions as func
import requests
import time
import json
import io
import os
import email.parser
from urllib.parse import parse_qs
import PyPDF2  # Added for PDF page counting

# Get credentials from environment variables with fallback to hardcoded values
subscription_key = os.environ.get('VISION_API_KEY', 'BU9HKSgK9GI0G6svRx8bPqs0t4Ra7MnFkULlglz3jNK7aMUQOgMlJQQJ99BCACPV0roXJ3w3AAAFACOGbna6')
endpoint = os.environ.get('VISION_API_ENDPOINT', 'https://heinocr-vision.cognitiveservices.azure.com/')
read_api_url = endpoint + "vision/v3.2/read/analyze"

def process_pdf_page(pdf_bytes, page_spec, subscription_key, endpoint):
    """Process specific pages of a PDF using Azure Vision API"""
    read_api_url = endpoint + "vision/v3.2/read/analyze"
    
    # Set up headers for Azure Vision API
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'application/pdf'
    }
    
    # Add parameters for processing specific pages
    params = {
        'pages': page_spec
    }
    
    logging.info(f"Calling Azure Vision API with params: {params}")
    
    # Send request to Azure Vision API
    response = requests.post(read_api_url, headers=headers, params=params, data=pdf_bytes)
    
    if response.status_code != 202:
        logging.error(f"Error: {response.status_code} - {response.text}")
        return None
    
    operation_url = response.headers["Operation-Location"]
    logging.info(f"Operation URL: {operation_url}")
    
    # Poll for results with timeout
    max_retries = 60  # 60 seconds timeout
    retry_count = 0
    
    while True:
        response_final = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key})
        analysis = response_final.json()
        
        if 'analyzeResult' in analysis:
            logging.info(f"✅ Analysis completed successfully for pages {page_spec}")
            break
        elif analysis.get('status') == 'failed':
            logging.error(f"❌ Analysis failed for pages {page_spec}: {json.dumps(analysis)}")
            return None
        elif retry_count >= max_retries:
            logging.error(f"❌ Analysis timed out after 60 seconds for pages {page_spec}")
            return None
        
        retry_count += 1
        time.sleep(1)
    
    if analysis.get('status') == 'succeeded':
        extracted_text = []
        page_count = len(analysis['analyzeResult']['readResults'])
        logging.info(f"✅ Successfully processed {page_count} pages for {page_spec}")
        
        # Process each page
        for page_result in analysis['analyzeResult']['readResults']:
            page_num = page_result['page']
            page_text = []
            
            for line in page_result['lines']:
                page_text.append(line['text'])
            
            # Add page separator
            page_content = "\n".join(page_text)
            extracted_text.append((page_num, page_content))
        
        return extracted_text
    else:
        logging.error(f"OCR extraction failed for pages {page_spec}.")
        return None

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get request parameters
        content_type = req.headers.get('Content-Type')
        body = req.get_body()
        
        # Parse multipart form data
        if content_type and 'multipart/form-data' in content_type:
            boundary = content_type.split('boundary=')[1].strip()
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]
                
            # Create a parser
            parser = email.parser.BytesParser()
            multipart_content = b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + body
            
            # Parse the multipart content
            parsed = parser.parse(io.BytesIO(multipart_content))
            
            # Extract file content and parameters
            pdf_bytes = None
            pages_param = None
            
            for part in parsed.get_payload():
                content_disposition = part.get('Content-Disposition', '')
                if 'name="file"' in content_disposition:
                    pdf_bytes = part.get_payload(decode=True)
                    logging.info(f"✅ PDF file received, size: {len(pdf_bytes)} bytes")
                elif 'name="pages"' in content_disposition:
                    pages_param = part.get_payload()
                    logging.info(f"Processing specific pages: {pages_param}")
            
            if not pdf_bytes:
                raise ValueError("No file attachment found in form data with name 'file'.")
        else:
            raise ValueError("Expected multipart/form-data content type")

        # Get the total number of pages in the PDF using PyPDF2
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        logging.info(f"Total pages in PDF (detected with PyPDF2): {total_pages}")
        
        # Reset the file pointer to the beginning of the file
        pdf_file.seek(0)
        
        all_results = []
        
        # Check if specific pages were requested
        if pages_param:
            # Use the specified pages parameter
            result = process_pdf_page(pdf_bytes, pages_param, subscription_key, endpoint)
            if result:
                all_results.extend(result)
        else:
            # No specific pages requested, implement the first page + last two pages approach
            if total_pages <= 2:
                # If the PDF has 1 or 2 pages, process all pages in a single request
                logging.info(f"PDF has only {total_pages} pages, processing all in one request")
                pages_to_process = f"1-{total_pages}"
                result = process_pdf_page(pdf_bytes, pages_to_process, subscription_key, endpoint)
                if result:
                    all_results.extend(result)
            else:
                # Process the first page in one request
                logging.info("Processing first page (page 1)")
                first_page_result = process_pdf_page(pdf_bytes, "1", subscription_key, endpoint)
                if first_page_result:
                    all_results.extend(first_page_result)
                
                # Process the last two pages in another request
                if total_pages >= 3:
                    last_two_pages = f"{total_pages-1}-{total_pages}"
                    logging.info(f"Processing last two pages (pages {last_two_pages})")
                    last_pages_result = process_pdf_page(pdf_bytes, last_two_pages, subscription_key, endpoint)
                    if last_pages_result:
                        all_results.extend(last_pages_result)
        
        if not all_results:
            logging.error("No results were obtained from any of the requests")
            return func.HttpResponse(
                json.dumps({"error": "Failed to extract text from PDF"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Sort results by page number
        all_results.sort(key=lambda x: x[0])
        
        # Format the final output
        formatted_results = []
        for page_num, content in all_results:
            if page_num == 1:
                page_label = "FIRST PAGE"
            else:
                page_label = f"LAST PAGES - Page {page_num} of {total_pages}"
            
            formatted_results.append(f"--- {page_label} ---\n{content}")
        
        result_text = "\n\n".join(formatted_results)
        
        return func.HttpResponse(
            json.dumps({
                "extracted_text": result_text,
                "page_count": len(all_results),
                "total_pdf_pages": total_pages,
                "processed_pages": [page for page, _ in all_results]
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❌ Error processing PDF: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        return func.HttpResponse(
            json.dumps({"error": str(e), "traceback": traceback.format_exc()}),
            status_code=500,
            mimetype="application/json"
        )
