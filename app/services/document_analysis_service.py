"""Document Analysis Service - AI-powered document intelligence."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """AI-powered document analysis for real estate."""

    async def analyze_document(
        self,
        file_path: str,
        document_type: str,
        property_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze a document with AI.

        Args:
            file_path: Path to document file
            document_type: Type (inspection_report, contract, appraisal, etc.)
            property_id: Optional property ID

        Returns:
            Analysis results
        """
        try:
            # Read document content
            content = self._read_document(file_path)

            if not content:
                return {"error": "Could not read document"}

            # Analyze based on document type
            if document_type == "inspection_report":
                return await self._analyze_inspection_report(content, property_id)
            elif document_type == "contract":
                return await self._analyze_contract(content, property_id)
            elif document_type == "appraisal":
                return await self._analyze_appraisal(content, property_id)
            else:
                return await self._analyze_general(content, document_type, property_id)

        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return {"error": str(e)}

    def _read_document(self, file_path: str) -> Optional[str]:
        """Read document content from file.

        Args:
            file_path: Path to document

        Returns:
            File content as string
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None

            # Read based on file extension
            if path.suffix.lower() == ".pdf":
                return self._read_pdf(file_path)
            elif path.suffix.lower() in [".doc", ".docx"]:
                return self._read_word(file_path)
            elif path.suffix.lower() == ".txt":
                return path.read_text()
            else:
                # Try as text
                return path.read_text()

        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return None

    def _read_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF

        Returns:
            Extracted text
        """
        try:
            import PyPDF2

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text

        except ImportError:
            logger.warning("PyPDF2 not installed, trying basic text extraction")
            # Fallback: try reading as binary and decode
            try:
                with open(file_path, 'rb') as f:
                    return f.read().decode('utf-8', errors='ignore')
            except:
                return None
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return None

    def _read_word(self, file_path: str) -> Optional[str]:
        """Extract text from Word document.

        Args:
            file_path: Path to Word doc

        Returns:
            Extracted text
        """
        try:
            from docx import Document

            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text

        except ImportError:
            logger.warning("python-docx not installed")
            return None
        except Exception as e:
            logger.error(f"Error reading Word doc: {e}")
            return None

    async def _analyze_inspection_report(
        self,
        content: str,
        property_id: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze inspection report and extract issues.

        Args:
            content: Inspection report text
            property_id: Optional property ID

        Returns:
            Analysis with issues found
        """
        client = llm_service.client

        prompt = f"""You are a real estate inspection expert. Analyze this inspection report and extract:

1. All issues found (categorized by severity: critical, major, minor)
2. Repair cost estimates for each issue
3. Safety hazards that require immediate attention
4. Recommended follow-up actions

Format your response as JSON:
{{
  "summary": "Brief overview of inspection",
  "issues": [
    {{
      "category": "electrical/plumbing/structural/etc",
      "description": "Issue description",
      "severity": "critical/major/minor",
      "estimated_cost": 500,
      "recommendation": "What to do"
    }}
  ],
  "total_estimated_cost": 5000,
  "critical_issues_count": 3,
  "safety_hazards": ["list of hazards"]
}}

Inspection Report:
{content[:10000]}  # Limit content size
"""

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Try to parse JSON response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    result["property_id"] = property_id
                    result["document_type"] = "inspection_report"
                    return result
            except:
                pass

            # Fallback: return raw analysis
            return {
                "property_id": property_id,
                "document_type": "inspection_report",
                "analysis": response_text,
                "raw_content": content[:500]  # First 500 chars
            }

        except Exception as e:
            logger.error(f"Error analyzing with Claude: {e}")
            return {
                "error": str(e),
                "property_id": property_id,
                "document_type": "inspection_report"
            }

    async def _analyze_contract(
        self,
        content: str,
        property_id: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze contract and extract key terms.

        Args:
            content: Contract text
            property_id: Optional property ID

        Returns:
            Extracted contract terms
        """
        client = llm_service.client

        prompt = f"""You are a real estate attorney. Analyze this contract and extract:

1. Parties involved (buyer, seller, agent)
2. Purchase price and terms
3. Contingencies and conditions
4. Key dates (closing, inspection period, etc.)
5. Special clauses or provisions
6. Potential risks or concerns

Format your response as JSON:
{{
  "parties": {{
    "buyer": "Name",
    "seller": "Name",
    "agent": "Name"
  }},
  "purchase_price": 500000,
  "price_terms": "Financing details",
  "contingencies": ["list of contingencies"],
  "key_dates": {{
    "closing_date": "2025-03-15",
    "inspection_period": "10 days"
  }},
  "special_clauses": ["list of clauses"],
  "risks": ["list of concerns"]
}}

Contract:
{content[:10000]}
"""

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Try to parse JSON response
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    result["property_id"] = property_id
                    result["document_type"] = "contract"
                    return result
            except:
                pass

            # Fallback
            return {
                "property_id": property_id,
                "document_type": "contract",
                "analysis": response_text
            }

        except Exception as e:
            logger.error(f"Error analyzing contract: {e}")
            return {"error": str(e)}

    async def _analyze_appraisal(
        self,
        content: str,
        property_id: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze appraisal report.

        Args:
            content: Appraisal text
            property_id: Optional property ID

        Returns:
            Appraisal analysis
        """
        client = llm_service.client

        prompt = f"""You are a real estate appraiser. Analyze this appraisal and extract:

1. Appraised value
2. Property details (beds, baths, sqft, lot size)
3. Comps used and their values
4. Adjustments made
5. Value calculation method
6. Final opinion of value

Format your response as JSON:
{{
  "appraised_value": 450000,
  "property_details": {{
    "bedrooms": 3,
    "bathrooms": 2,
    "square_feet": 1800,
    "lot_size": 5000
  }},
  "comps": [
    {{
      "address": "123 Main St",
      "sale_price": 440000,
      "adjustments": "Square footage +10000"
    }}
  ],
  "value_method": "sales comparison approach",
  "final_opinion": "Summary of value"
}}

Appraisal:
{content[:10000]}
"""

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Try to parse JSON
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    result["property_id"] = property_id
                    result["document_type"] = "appraisal"
                    return result
            except:
                pass

            return {
                "property_id": property_id,
                "document_type": "appraisal",
                "analysis": response_text
            }

        except Exception as e:
            logger.error(f"Error analyzing appraisal: {e}")
            return {"error": str(e)}

    async def _analyze_general(
        self,
        content: str,
        document_type: str,
        property_id: Optional[int]
    ) -> Dict[str, Any]:
        """General document analysis.

        Args:
            content: Document text
            document_type: Document type
            property_id: Optional property ID

        Returns:
            General analysis
        """
        client = llm_service.client

        prompt = f"""Analyze this {document_type} and provide:
1. Summary of key points
2. Important dates or deadlines
3. Action items or requirements
4. Any concerns or risks

Document:
{content[:10000]}
"""

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            return {
                "property_id": property_id,
                "document_type": document_type,
                "summary": response_text
            }

        except Exception as e:
            logger.error(f"Error in general analysis: {e}")
            return {"error": str(e)}

    async def compare_documents(
        self,
        file_path_1: str,
        file_path_2: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Compare two documents and highlight differences.

        Args:
            file_path_1: First document
            file_path_2: Second document
            document_type: Type of documents

        Returns:
            Comparison results
        """
        content_1 = self._read_document(file_path_1)
        content_2 = self._read_document(file_path_2)

        if not content_1 or not content_2:
            return {"error": "Could not read one or both documents"}

        client = llm_service.client

        prompt = f"""Compare these two {document_type}s and highlight:

1. Key differences
2. Discrepancies in values, dates, or terms
3. Which is more favorable and why
4. Recommendations

Document 1:
{content_1[:5000]}

Document 2:
{content_2[:5000]}
"""

        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            return {
                "document_type": document_type,
                "comparison": response_text
            }

        except Exception as e:
            logger.error(f"Error comparing documents: {e}")
            return {"error": str(e)}

    async def chat_with_document(
        self,
        file_path: str,
        question: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Q&A with a document.

        Args:
            file_path: Path to document
            question: User's question
            chat_history: Optional conversation history

        Returns:
            Answer to question
        """
        content = self._read_document(file_path)

        if not content:
            return {"error": "Could not read document"}

        client = llm_service.client

        # Build conversation
        messages = []

        # Add context
        messages.append({
            "role": "user",
            "content": f"""I'm going to ask you questions about this document. Please answer based only on the document content.

Document:
{content[:15000]}
"""
        })

        # Add chat history
        if chat_history:
            for item in chat_history:
                messages.append({"role": item["role"], "content": item["content"]})

        # Add current question
        messages.append({"role": "user", "content": question})

        try:
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=messages
            )

            answer = response.content[0].text

            return {
                "question": question,
                "answer": answer,
                "document": file_path
            }

        except Exception as e:
            logger.error(f"Error in document chat: {e}")
            return {"error": str(e)}


document_analysis_service = DocumentAnalysisService()
