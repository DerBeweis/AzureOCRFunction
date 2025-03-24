# Azure OCR Function

This is a serverless Azure Function that processes PDF files using Azure Computer Vision API for OCR.

## Azure Services Used

1. **Azure Functions**
   - Runtime: Python
   - Hosting: Serverless
   - Trigger: HTTP

2. **Azure Computer Vision**
   - API Version: v3.2
   - Service: Read API
   - Endpoint: Custom (configured in code)

## Subscription Requirements

### 1. Azure Functions
- No additional subscription required
- Included in Azure Functions pricing
- Pay-per-execution model

### 2. Azure Computer Vision
- **Subscription Key**: Required
- **Endpoint URL**: Required
- **Pricing Tier**: Choose based on usage
  - F0 (Free tier): 5000 transactions per month
  - S0: Pay-per-transaction
  - S1: Higher throughput capacity

## Configuration

The Azure Computer Vision subscription key and endpoint are currently hardcoded in the code. For production deployment, these should be moved to environment variables or Azure Key Vault.

## Dependencies

- azure-functions==1.21.3
- requests==2.32.3

## Usage

1. Deploy the function to Azure
2. The function expects a POST request with a PDF file in the form-data with key 'file'
3. Returns the extracted text from the PDF

## Security Notes

- Move Azure Computer Vision credentials to secure storage (Key Vault)
- Implement proper authentication for the function endpoint
- Monitor usage to avoid exceeding service limits
