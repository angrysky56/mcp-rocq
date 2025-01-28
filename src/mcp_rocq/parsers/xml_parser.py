"""
XML Parser for Coq responses.
Handles structured communication with Coq's XML protocol.
"""
from typing import Dict
from xml.etree import ElementTree as ET

class CoqXMLParser:
    @staticmethod
    def parse_response(xml_str: str) -> Dict:
        """
        Parse Coq's XML protocol response into structured data
        
        Args:
            xml_str: Raw XML response from Coq
            
        Returns:
            Dict containing parsed response with status and message
        """
        try:
            root = ET.fromstring(xml_str)
            if root.tag == "value":
                return {
                    "status": "success",
                    "message": root.text,
                    "response_type": root.get("val")
                }
            elif root.tag == "feedback":
                return {
                    "status": "feedback",
                    "message": root.find("message").text,
                    "level": root.get("object")
                }
            elif root.tag == "error":
                return {
                    "status": "error", 
                    "message": root.find("message").text
                }
            
            return {"status": "unknown", "message": xml_str}
            
        except ET.ParseError as e:
            return {"status": "error", "message": f"XML parse error: {e}"}
