# Azure OCR Function

This is a serverless Azure Function that processes PDF files using Azure Computer Vision API for OCR with intelligent page selection.

## Azure Services Used

1. **Azure Functions**
   - Runtime: Python
   - Hosting: Serverless
   - Trigger: HTTP

2. **Azure Computer Vision**
   - API Version: v3.2
   - Service: Read API
   - Endpoint: Custom (configured in code)

## Key Features

1. **Smart Page Selection**
   - Uses PyPDF2 to determine the total page count of PDF documents
   - Processes only the first page and last two pages to optimize API usage
   - Handles PDFs with fewer than 3 pages appropriately
   - Ideal for extracting key information while staying within free tier limits

2. **Enhanced Response Format**
   - Clearly labels which pages were processed (FIRST PAGE, LAST PAGES)
   - Returns comprehensive metadata including total page count and processed pages
   - Provides JSON response with structured data

## Subscription Requirements

### 1. Azure Functions
- No additional subscription required
- Included in Azure Functions pricing
- Pay-per-execution model

### 2. Azure Computer Vision
- **Subscription Key**: Required
- **Endpoint URL**: Required
- **Pricing Tier**: Choose based on usage
  - F0 (Free tier): 500 transactions per month, limited to 2 pages per request
  - S0: Pay-per-transaction
  - S1: Higher throughput capacity

## Configuration

The Azure Computer Vision subscription key and endpoint are configured to use environment variables with fallback to hardcoded values. For production deployment, these should be moved to Azure Key Vault.

```python
subscription_key = os.environ.get('VISION_API_KEY', 'your-key-here')
endpoint = os.environ.get('VISION_API_ENDPOINT', 'your-endpoint-here')
```

## Dependencies

- azure-functions==1.21.3
- requests==2.32.3
- PyPDF2==3.0.1

## Usage

1. Deploy the function to Azure
2. The function expects a POST request with a PDF file in the form-data with key 'file'
3. Optionally, you can specify which pages to process with a 'pages' parameter
4. Returns a JSON response with:
   - extracted_text: The OCR-extracted text with page labels
   - page_count: Number of pages processed
   - total_pdf_pages: Total number of pages in the PDF
   - processed_pages: List of page numbers that were processed

## Example Response

```json
{
  "extracted_text": "--- FIRST PAGE ---\nContent from first page...\n\n--- LAST PAGES - Page 9 of 10 ---\nContent from page 9...\n\n--- LAST PAGES - Page 10 of 10 ---\nContent from page 10...",
  "page_count": 3,
  "total_pdf_pages": 10,
  "processed_pages": [1, 9, 10]
}
```

## Security Notes

- Move Azure Computer Vision credentials to secure storage (Key Vault)
- Implement proper authentication for the function endpoint
- Monitor usage to avoid exceeding service limits
