"""
Document AI Extraction Service
Uses OCR and LLM to extract data from PDFs and images
"""
import os
import io
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import tempfile

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.config import settings


class DocumentExtractor:
    """
    Extract structured data from documents using OCR + LLM
    Supports: PDF, PNG, JPG, JPEG
    """

    def __init__(self):
        self.anthropic = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.use_aws_textract = AWS_AVAILABLE and os.getenv("AWS_REGION")

    async def extract_from_file(
        self,
        file_content: bytes,
        file_type: str,
        extraction_type: str = "property"
    ) -> Dict[str, Any]:
        """
        Extract structured data from uploaded file

        Args:
            file_content: File bytes
            file_type: File type (pdf, png, jpg, jpeg)
            extraction_type: Type of extraction (property, contract, contact)

        Returns:
            Extracted data as dictionary
        """
        # Step 1: Extract text from document
        text = await self._ocr_extract(file_content, file_type)

        if not text or len(text.strip()) < 50:
            return {
                "success": False,
                "error": "Could not extract sufficient text from document",
                "raw_text": text
            }

        # Step 2: Use LLM to structure the data
        structured_data = await self._llm_extract(text, extraction_type)

        return {
            "success": True,
            "raw_text": text,
            "structured_data": structured_data,
            "extraction_type": extraction_type
        }

    async def _ocr_extract(self, file_content: bytes, file_type: str) -> str:
        """Extract text using OCR (Tesseract or AWS Textract)"""

        # Try AWS Textract first (more accurate)
        if self.use_aws_textract:
            try:
                return await self._aws_textract(file_content)
            except Exception as e:
                print(f"AWS Textract failed: {e}, falling back to Tesseract")

        # Fall back to Tesseract
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("OCR not available - install pytesseract or configure AWS")

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            if file_type == "pdf":
                # Convert PDF to images
                images = convert_from_path(tmp_path, dpi=200)
                text_parts = []
                for img in images:
                    text_parts.append(pytesseract.image_to_string(img))
                return "\n".join(text_parts)
            else:
                # Direct image OCR
                image = Image.open(tmp_path)
                return pytesseract.image_to_string(image)
        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

    async def _aws_textract(self, file_content: bytes) -> str:
        """Extract text using AWS Textract"""
        if not AWS_AVAILABLE:
            raise RuntimeError("boto3 not installed")

        client = boto3.client('textract', region_name=os.getenv("AWS_REGION"))

        response = client.detect_document_text(
            Document={'Bytes': file_content}
        )

        # Extract all text blocks
        text_parts = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_parts.append(block['Text'])

        return '\n'.join(text_parts)

    async def _llm_extract(self, text: str, extraction_type: str) -> Dict[str, Any]:
        """Use Claude LLM to structure extracted text"""

        if not self.anthropic:
            return {"error": "Anthropic API not configured"}

        prompts = {
            "property": self._property_prompt(),
            "contract": self._contract_prompt(),
            "contact": self._contact_prompt()
        }

        prompt = prompts.get(extraction_type, prompts["property"])

        try:
            message = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{prompt}\n\nDocument text:\n{text}"
                            }
                        ]
                    }
                ]
            )

            # Extract JSON from response
            response_text = message.content[0].text
            return self._parse_json_response(response_text)

        except Exception as e:
            return {
                "error": f"LLM extraction failed: {str(e)}",
                "raw_response": str(e)
            }

    def _property_prompt(self) -> str:
        return """You are a real estate document parser. Extract property information from the document and return ONLY a valid JSON object.

Extract these fields if present:
- address: Full street address
- city: City name
- state: State abbreviation
- zip_code: ZIP code
- price: Listing price (as number, no symbols)
- bedrooms: Number of bedrooms (as integer)
- bathrooms: Number of bathrooms (as float)
- square_feet: Living area in sqft (as integer)
- year_built: Year built (as integer)
- lot_size: Lot size in acres or sqft (as float)
- property_type: One of: HOUSE, CONDO, TOWNHOUSE, APARTMENT, LAND, COMMERCIAL
- description: Property description text
- listing_id: MLS or listing ID if present

Return ONLY the JSON object, no other text. Use null for missing values."""

    def _contract_prompt(self) -> str:
        return """You are a legal document parser. Extract contract information and return ONLY a valid JSON object.

Extract these fields if present:
- title: Contract title or type
- parties: List of parties involved (buyer, seller, etc.)
- contract_date: Date of contract (YYYY-MM-DD)
- effective_date: Effective date (YYYY-MM-DD)
- expiration_date: Expiration date (YYYY-MM-DD)
- amount: Contract amount (as number, no symbols)
- terms: Key terms and conditions
- clauses: List of important clause names

Return ONLY the JSON object, no other text. Use null for missing values."""

    def _contact_prompt(self) -> str:
        return """You are a contact information parser. Extract contact details and return ONLY a valid JSON object.

Extract these fields if present:
- full_name: Person's full name
- email: Email address
- phone: Phone number(s) - return as array
- company: Company or organization name
- title: Job title or role
- address: Mailing address
- role: One of: buyer, seller, attorney, inspector, appraiser, contractor, lender, title_company, other

Return ONLY the JSON object, no other text. Use null for missing values."""

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "error": "Could not parse JSON from LLM response",
            "raw_response": response
        }

    async def extract_multiple_fields(
        self,
        text: str,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract specific fields from text

        Args:
            text: Text to extract from
            fields: List of field names to extract

        Returns:
            Dictionary with extracted values
        """
        prompt = f"""Extract the following fields from the text: {', '.join(fields)}

Return ONLY a JSON object with these exact field names.
Use null if a field is not found.

Text:
{text}"""

        if not self.anthropic:
            return {"error": "Anthropic API not configured"}

        try:
            message = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            return self._parse_json_response(response_text)

        except Exception as e:
            return {"error": str(e)}


# Singleton instance
document_extractor = DocumentExtractor()


async def extract_from_upload(
    file_content: bytes,
    file_type: str,
    extraction_type: str = "property"
) -> Dict[str, Any]:
    """
    Convenience function for document extraction

    Usage:
        from app.services.document_extraction import extract_from_upload

        result = await extract_from_upload(
            file_content=pdf_bytes,
            file_type="pdf",
            extraction_type="property"
        )

        if result["success"]:
            property_data = result["structured_data"]
            # Create property with extracted data
    """
    return await document_extractor.extract_from_file(
        file_content=file_content,
        file_type=file_type,
        extraction_type=extraction_type
    )
