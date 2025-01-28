"""
Type checking handler for Coq integration
Supports dependent type checking and verification
"""
from typing import Optional, Dict, List
import logging

from .coq_session import CoqSession

logger = logging.getLogger(__name__)

class TypeChecker:
    def __init__(self, coq: CoqSession):
        self.coq = coq
        
    async def check_type(self, term: str, expected_type: Optional[str] = None,
                        context: Optional[List[str]] = None) -> Dict:
        """
        Check types using Coq's dependent type system
        
        Args:
            term: Term to type check
            expected_type: Optional expected type to verify against
            context: Optional list of modules to import
            
        Returns:
            Dict containing type checking result
        """
        try:
            # Import context modules if provided
            if context:
                for module in context:
                    result = await self.coq.send_command(f'Require Import {module}.')
                    if not result:
                        return result.parsed
            
            # First check if term is well-formed
            check_cmd = f'Check ({term}).'
            result = await self.coq.send_command(check_cmd)
            if not result:
                return result.parsed
                
            # Verify against expected type if provided
            if expected_type:
                verify_cmd = f'Check ({term}) : {expected_type}.'
                result = await self.coq.send_command(verify_cmd)
                
            return result.parsed
            
        except Exception as e:
            logger.error(f"Type check error: {e}")
            return {"status": "error", "message": str(e)}