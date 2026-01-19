import os
import json
from typing import Optional

try:
    from docling.document_converter import DocumentConverter
    from docling_core.types.doc import DoclingDocument
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Warning: docling not installed. Please install it using `pip install docling`.")

class DoclingProcessor:
    def __init__(self):
        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
        else:
            self.converter = None

    def process(self, file_path: str):
        """
        Processes a file using Docling.
        Returns Docling ConversionResult for PDFs/HTML/etc.
        Returns str for .txt and .json.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        file_ext = os.path.splitext(file_path)[1].lower()

        # Handle .txt files directly
        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file: {e}")
                return None

        if file_ext == '.json':
            return self._process_json(file_path)

        if not DOCLING_AVAILABLE:
            return None

        print(f"Processing {file_path} with Docling...")
        try:
            # Returns docling.document_converter.ConversionResult
            result = self.converter.convert(file_path)
            return result
        except Exception as e:
            print(f"Error processing file with Docling: {e}")
            return None

    def _process_json(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            print(f"Error processing JSON: {e}")
            return ""
