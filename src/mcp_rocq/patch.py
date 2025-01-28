"""Manages a Coq session and XML protocol communication"""
import asyncio
import logging
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Union, List

logger = logging.getLogger(__name__)

class CoqCommand:
    """XML formatted Coq command"""
    @staticmethod
    def init() -> str:
        return '<call val="init"><option val="none"/></call>'
        
    @staticmethod
    def interp(cmd: str) -> str:
        escaped_cmd = cmd.replace('"', '&quot;')
        return f'''
        <call val="interp">
            <pair>
                <string>{escaped_cmd}</string>
                <union val="in_script"><unit/></union>
            </pair>
        </call>
        '''.strip()
        
    @staticmethod
    def check(term: str) -> str:
        return CoqCommand.interp(f"Check {term}.")
        
    @staticmethod
    def require(module: str) -> str:
        return CoqCommand.interp(f"Require Import {module}.")

class CoqResponse:
    """Structured response from Coq's XML protocol"""
    def __init__(self, xml_str: str):
        self.raw = xml_str
        self.parsed = self._parse_xml(xml_str)
        
    def _parse_xml(self, xml_str: str) -> Dict:
        try:
            root = ET.fromstring(xml_str)
            
            # Handle different response types
            if root.tag == "value":
                val_type = root.get("val", "")
                if val_type == "good":
                    # Success response
                    return {
                        "status": "success",
                        "message": self._extract_message(root),
                        "response_type": val_type
                    }
                elif val_type == "fail":
                    # Error response
                    return {
                        "status": "error",
                        "message": self._extract_message(root),
                        "error_type": root.find(".//string").get("val", "unknown")
                    }
                    
            elif root.tag == "feedback":
                # Feedback message
                return {
                    "status": "feedback",
                    "level": root.get("object", "info"),
                    "message": self._extract_message(root.find("message"))
                }
                
            return {"status": "unknown", "message": xml_str}
            
        except ET.ParseError as e:
            return {"status": "error", "message": f"XML parse error: {e}"}
            
    def _extract_message(self, elem: ET.Element) -> str:
        """Extract message content from XML element"""
        if elem is None:
            return ""
        if elem.text:
            return elem.text.strip()
        msg_elem = elem.find(".//string")
        if msg_elem is not None and msg_elem.text:
            return msg_elem.text.strip()
        return ""

    @property
    def status(self) -> str:
        return self.parsed["status"]
        
    @property
    def message(self) -> str:
        return self.parsed["message"]
        
    def __bool__(self) -> bool:
        return self.status == "success"

class CoqSession:
    """Manages interaction with a Coq process using XML protocol"""
    
    def __init__(self, coq_path: Path, lib_path: Path):
        self.coq_path = coq_path
        self.lib_path = lib_path
        self.process: Optional[subprocess.Popen] = None
        self._start_coq()
        self._init_session()

    def _start_coq(self):
        """Start Coq process with XML protocol"""
        try:
            cmd = [
                str(self.coq_path),
                "-xml",  # Use XML protocol
                "-Q", str(self.lib_path), "Coq"
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Coq process started successfully")
            
            # Read initial banner
            self._read_until_prompt()
            
        except Exception as e:
            logger.error(f"Failed to start Coq: {e}")
            raise
            
    def _init_session(self):
        """Initialize Coq session with XML protocol"""
        init_cmd = CoqCommand.init()
        response = self._send_raw(init_cmd)
        if not response:
            raise RuntimeError(f"Failed to initialize Coq session: {response.message}")
            
    def _read_until_prompt(self) -> List[str]:
        """Read output until we get a complete XML response"""
        response = []
        depth = 0
        
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
                
            response.append(line)
            
            # Track XML element depth
            depth += line.count("<") - line.count("</")
            if depth == 0 and response:
                break
                
        return response

    async def send_command(self, cmd: str) -> CoqResponse:
        """Send command to Coq and get response"""
        if not self.process:
            raise RuntimeError("Coq process not running")
            
        xml_cmd = CoqCommand.interp(cmd)
        return self._send_raw(xml_cmd)
        
    def _send_raw(self, xml: str) -> CoqResponse:
        """Send raw XML command and get response"""
        try:
            self.process.stdin.write(xml + "\n")
            self.process.stdin.flush()
            
            response = self._read_until_prompt()
            return CoqResponse("".join(response))
            
        except Exception as e:
            logger.error(f"Command error: {e}")
            return CoqResponse(f'<value val="fail"><string>Error: {str(e)}</string></value>')

    async def close(self):
        """Clean up Coq process"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.sleep(0.1)  # Give process time to terminate
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error closing Coq process: {e}")
                if self.process:
                    self.process.kill()  # Force kill if needed