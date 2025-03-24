import logging
import azure.functions as func
import requests
import time
import json
import cgi
import io  

subscription_key = 'BU9HKSgK9GI0G6svRx8bPqs0t4Ra7MnFkULlglz3jNK7aMUQOgMlJQQJ99BCACPV0roXJ3w3AAAFACOGbna6'
endpoint = 'https://heinocr-vision.cognitiveservices.azure.com/'
read_api_url = endpoint + "vision/v3.2/read/analyze"

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        content_type = req.headers.get('Content-Type')
        body = req.get_body()
        fp = io.BytesIO(body)  

        env = {'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
        form = cgi.FieldStorage(fp=fp, environ=env)

        fileitem = form["file"]
        if fileitem.file:
            pdf_bytes = fileitem.file.read()
        else:
            raise ValueError("No file attachment found clearly in part 2 named 'file'.")

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/pdf'
        }

        response = requests.post(read_api_url, headers=headers, data=pdf_bytes)
        response.raise_for_status()

        operation_url = response.headers["Operation-Location"]

        while True:
            response_final = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key})
            analysis = response_final.json()
            if 'analyzeResult' in analysis or analysis.get('status') == 'failed':
                break
            time.sleep(1)

        if analysis.get('status') == 'succeeded':
            extracted_text = []
            for page in analysis['analyzeResult']['readResults']:
                for line in page['lines']:
                    extracted_text.append(line['text'])
            result_text = "\n".join(extracted_text)
            logging.info("✅ OCR extraction succeeded.")
        else:
            result_text = "OCR extraction failed."
            logging.error("❌ OCR extraction failed.")


        clean_text = result_text.replace("\n", " ").strip()

        return func.HttpResponse(
        json.dumps({"extracted_text": clean_text}),
        status_code=200,
        mimetype="application/json"
)


    except Exception as e:
        logging.error(f"❌ Error processing PDF: {e}")
        return func.HttpResponse(
            json.dumps({"extracted_text": f"Error processing PDF: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
