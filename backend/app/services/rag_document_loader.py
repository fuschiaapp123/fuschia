"""
RAG Document Loader Service
Loads and chunks documents from various sources (local files, URLs)
"""

import os
import re
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog
import httpx
from bs4 import BeautifulSoup

from app.models.rag_config import DocumentChunk, DataSourceType

logger = structlog.get_logger()


class DocumentLoader:
    """Service for loading documents from various sources"""

    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx', '.csv', '.json', '.html'}

    def __init__(self):
        self.logger = logger.bind(service="DocumentLoader")

    async def load_documents(
        self,
        data_source_type: DataSourceType,
        data_source_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[DocumentChunk]:
        """Load and chunk documents from the specified source"""

        if data_source_type == DataSourceType.NONE or not data_source_path:
            self.logger.info("No data source specified, returning empty chunks")
            return []

        try:
            if data_source_type == DataSourceType.LOCAL_FILE:
                return await self._load_local_files(data_source_path, chunk_size, chunk_overlap)
            elif data_source_type == DataSourceType.URL:
                return await self._load_from_url(data_source_path, chunk_size, chunk_overlap)
            else:
                self.logger.warning(f"Unknown data source type: {data_source_type}")
                return []
        except Exception as e:
            self.logger.error("Failed to load documents", error=str(e), source=data_source_path)
            raise

    async def _load_local_files(
        self,
        path: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Load documents from local file or directory"""

        chunks = []
        path_obj = Path(path)

        if not path_obj.exists():
            self.logger.warning(f"Path does not exist: {path}")
            return []

        if path_obj.is_file():
            file_chunks = await self._load_single_file(path_obj, chunk_size, chunk_overlap)
            chunks.extend(file_chunks)
        elif path_obj.is_dir():
            for file_path in path_obj.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    file_chunks = await self._load_single_file(file_path, chunk_size, chunk_overlap)
                    chunks.extend(file_chunks)

        self.logger.info(f"Loaded {len(chunks)} chunks from local files", path=path)
        return chunks

    async def _load_single_file(
        self,
        file_path: Path,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Load and chunk a single file"""

        try:
            suffix = file_path.suffix.lower()

            if suffix == '.pdf':
                content = await self._load_pdf(file_path)
            elif suffix == '.docx':
                content = await self._load_docx(file_path)
            elif suffix in {'.txt', '.md', '.csv', '.json'}:
                content = await self._load_text_file(file_path)
            elif suffix == '.html':
                content = await self._load_html_file(file_path)
            else:
                self.logger.warning(f"Unsupported file type: {suffix}")
                return []

            return self._chunk_text(content, str(file_path), chunk_size, chunk_overlap)

        except Exception as e:
            self.logger.error(f"Failed to load file: {file_path}", error=str(e))
            return []

    async def _load_text_file(self, file_path: Path) -> str:
        """Load a plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    async def _load_html_file(self, file_path: Path) -> str:
        """Load and extract text from HTML file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return self._extract_text_from_html(html_content)

    async def _load_pdf(self, file_path: Path) -> str:
        """Load text from PDF file"""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n\n'.join(text_parts)
        except ImportError:
            self.logger.warning("pypdf not installed, skipping PDF file")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to load PDF: {file_path}", error=str(e))
            return ""

    async def _load_docx(self, file_path: Path) -> str:
        """Load text from DOCX file"""
        try:
            import docx
            doc = docx.Document(str(file_path))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(paragraphs)
        except ImportError:
            self.logger.warning("python-docx not installed, skipping DOCX file")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to load DOCX: {file_path}", error=str(e))
            return ""

    async def _load_from_url(
        self,
        url: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Load documents from URL"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                content_type = response.headers.get('content-type', '')

                if 'text/html' in content_type:
                    text = self._extract_text_from_html(response.text)
                elif 'application/json' in content_type:
                    text = response.text
                elif 'text/plain' in content_type or 'text/markdown' in content_type:
                    text = response.text
                else:
                    # Try to extract text anyway
                    text = response.text

                chunks = self._chunk_text(text, url, chunk_size, chunk_overlap)
                self.logger.info(f"Loaded {len(chunks)} chunks from URL", url=url)
                return chunks

        except Exception as e:
            self.logger.error(f"Failed to load URL: {url}", error=str(e))
            return []

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text
        text = soup.get_text(separator='\n')

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def _chunk_text(
        self,
        text: str,
        source: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Split text into overlapping chunks"""

        if not text or not text.strip():
            return []

        # Clean the text
        text = self._clean_text(text)

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Find the end of this chunk
            end = start + chunk_size

            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind('. ', start, end),
                        text.rfind('! ', start, end),
                        text.rfind('? ', start, end),
                        text.rfind('.\n', start, end)
                    )
                    if sentence_break > start + chunk_size // 2:
                        end = sentence_break + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_id = hashlib.md5(f"{source}:{chunk_index}:{chunk_text[:50]}".encode()).hexdigest()

                chunks.append(DocumentChunk(
                    id=chunk_id,
                    content=chunk_text,
                    metadata={
                        'source': source,
                        'chunk_index': chunk_index,
                        'char_start': start,
                        'char_end': end
                    },
                    source=source,
                    chunk_index=chunk_index
                ))
                chunk_index += 1

            # Move start position with overlap
            start = end - chunk_overlap if end < len(text) else len(text)

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text.strip()


# Singleton instance
document_loader = DocumentLoader()
