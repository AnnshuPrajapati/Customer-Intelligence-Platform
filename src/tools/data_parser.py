"""
Data Parser Tool.

This module provides utilities for parsing and preprocessing various data formats
used in the customer intelligence platform.
"""

import json
import csv
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import xml.etree.ElementTree as ET


class DataParser:
    """
    Utility class for parsing and preprocessing different data formats.

    Supports JSON, CSV, XML, and other common data formats used in
    customer feedback analysis.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data parser.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.supported_formats = ['json', 'csv', 'xml', 'txt']

    def parse_file(self, file_path: Union[str, Path], format_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a file based on its format.

        Args:
            file_path: Path to the file to parse
            format_type: Optional format specification (auto-detected if not provided)

        Returns:
            Dictionary containing parsed data and metadata

        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect format if not specified
        if not format_type:
            format_type = self._detect_format(file_path)

        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")

        # Parse based on format
        if format_type == 'json':
            data = self._parse_json(file_path)
        elif format_type == 'csv':
            data = self._parse_csv(file_path)
        elif format_type == 'xml':
            data = self._parse_xml(file_path)
        elif format_type == 'txt':
            data = self._parse_text(file_path)

        return {
            "data": data,
            "metadata": {
                "source_file": str(file_path),
                "format": format_type,
                "record_count": len(data) if isinstance(data, list) else 1,
                "parsed_at": pd.Timestamp.now().isoformat()
            }
        }

    def parse_multiple_files(self, file_paths: List[Union[str, Path]],
                           format_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse multiple files and combine the results.

        Args:
            file_paths: List of file paths to parse
            format_type: Optional format specification

        Returns:
            Dictionary containing combined parsed data
        """
        combined_data = []
        metadata_list = []

        for file_path in file_paths:
            result = self.parse_file(file_path, format_type)
            combined_data.extend(result["data"])
            metadata_list.append(result["metadata"])

        return {
            "data": combined_data,
            "metadata": {
                "source_files": [meta["source_file"] for meta in metadata_list],
                "total_records": len(combined_data),
                "parsed_at": pd.Timestamp.now().isoformat(),
                "file_details": metadata_list
            }
        }

    def _detect_format(self, file_path: Path) -> str:
        """
        Auto-detect file format based on extension.

        Args:
            file_path: Path to the file

        Returns:
            Detected format string
        """
        extension = file_path.suffix.lower().lstrip('.')

        format_mapping = {
            'json': 'json',
            'csv': 'csv',
            'xml': 'xml',
            'txt': 'txt'
        }

        return format_mapping.get(extension, 'txt')

    def _parse_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            List of parsed records
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # If it's a single object, wrap it in a list
            return [data]
        else:
            raise ValueError(f"Unexpected JSON structure in {file_path}")

    def _parse_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of parsed records
        """
        # Read CSV with pandas for better handling
        df = pd.read_csv(file_path, encoding='utf-8')

        # Convert to list of dictionaries
        records = df.to_dict('records')

        # Clean up data types and handle missing values
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, float) and value.is_integer():
                    record[key] = int(value)

        return records

    def _parse_xml(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse XML file.

        Args:
            file_path: Path to XML file

        Returns:
            List of parsed records
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        records = []

        # Convert XML elements to dictionaries
        for elem in root:
            record = self._xml_element_to_dict(elem)
            records.append(record)

        return records

    def _xml_element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary.

        Args:
            element: XML element

        Returns:
            Dictionary representation
        """
        result = {}

        # Add element attributes
        if element.attrib:
            result.update(element.attrib)

        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)

            # Handle multiple elements with same tag
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        # Add text content if no children
        if element.text and element.text.strip() and not element:
            result['text'] = element.text.strip()

        return result

    def _parse_text(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse plain text file.

        Args:
            file_path: Path to text file

        Returns:
            List containing text content
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return [{
            "content": content,
            "source": str(file_path),
            "type": "text"
        }]

    def validate_data_structure(self, data: List[Dict[str, Any]],
                              required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate the structure of parsed data.

        Args:
            data: Parsed data to validate
            required_fields: Optional list of required fields

        Returns:
            Validation results
        """
        if not data:
            return {
                "valid": False,
                "errors": ["No data provided"],
                "warnings": []
            }

        errors = []
        warnings = []

        # Check if data is a list
        if not isinstance(data, list):
            errors.append("Data must be a list of records")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check each record
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                errors.append(f"Record {i} is not a dictionary")
                continue

            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in record]
                if missing_fields:
                    errors.append(f"Record {i} missing required fields: {missing_fields}")

            # Check for empty records
            if not record:
                warnings.append(f"Record {i} is empty")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "record_count": len(data),
            "field_coverage": self._analyze_field_coverage(data)
        }

    def _analyze_field_coverage(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analyze field coverage across all records.

        Args:
            data: List of records to analyze

        Returns:
            Dictionary with field coverage percentages
        """
        if not data:
            return {}

        all_fields = set()
        field_counts = {}

        for record in data:
            for field in record.keys():
                all_fields.add(field)
                field_counts[field] = field_counts.get(field, 0) + 1

        total_records = len(data)
        coverage = {
            field: (count / total_records) * 100
            for field, count in field_counts.items()
        }

        return coverage

    def normalize_data(self, data: List[Dict[str, Any]],
                      field_mappings: Optional[Dict[str, str]] = None,
                      data_types: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Normalize data by applying field mappings and type conversions.

        Args:
            data: Data to normalize
            field_mappings: Optional field name mappings
            data_types: Optional data type specifications

        Returns:
            Normalized data
        """
        normalized_data = []

        for record in data.copy():
            # Apply field mappings
            if field_mappings:
                for old_field, new_field in field_mappings.items():
                    if old_field in record:
                        record[new_field] = record.pop(old_field)

            # Apply data type conversions
            if data_types:
                for field, dtype in data_types.items():
                    if field in record and record[field] is not None:
                        record[field] = self._convert_data_type(record[field], dtype)

            normalized_data.append(record)

        return normalized_data

    def _convert_data_type(self, value: Any, target_type: str) -> Any:
        """
        Convert value to specified data type.

        Args:
            value: Value to convert
            target_type: Target data type

        Returns:
            Converted value
        """
        try:
            if target_type == 'int':
                return int(float(value))
            elif target_type == 'float':
                return float(value)
            elif target_type == 'str':
                return str(value)
            elif target_type == 'bool':
                return bool(value)
            else:
                return value
        except (ValueError, TypeError):
            return value

    def export_data(self, data: List[Dict[str, Any]], output_path: Union[str, Path],
                   format_type: str = 'json') -> str:
        """
        Export data to a file.

        Args:
            data: Data to export
            output_path: Output file path
            format_type: Output format (json, csv)

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)

        if format_type == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == 'csv':
            if data:
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

        return str(output_path)
