"""
Property proving handler with custom tactics support
Provides automated and custom tactic-based proving capabilities
"""
from typing import Dict, List, Optional
import logging

from .coq_session import CoqSession

logger = logging.getLogger(__name__)

class ProofHandler:
    def __init__(self, coq: CoqSession):
        self.coq = coq
        
    async def prove_property(self, property_stmt: str, 
                           tactics: Optional[List[str]] = None,
                           use_automation: bool = True) -> Dict:
        """
        Prove properties using custom tactics and automation
        
        Args:
            property_stmt: Property to prove
            tactics: Optional list of custom tactics
            use_automation: Whether to try automated proving
            
        Returns:
            Dict containing proof result
        """
        try:
            # Start theorem
            result = await self.coq.send_command(f'Theorem property: {property_stmt}.')
            if not result:
                return result.parsed
            
            # Apply custom tactics if provided
            if tactics:
                for tactic in tactics:
                    result = await self.coq.send_command(tactic)
                    if not result:
                        await self.coq.send_command("Abort.")
                        return result.parsed
                    
            if use_automation:
                # Try automated proving strategies
                auto_tactics = [
                    "auto with *.",
                    "firstorder.",
                    "tauto.",
                    "intuition auto.",
                    "congruence."
                ]
                
                for tactic in auto_tactics:
                    result = await self.coq.send_command(tactic)
                    if "No more subgoals" in result.message:
                        break
                        
                    # If automation fails, try next tactic
                    if not result:
                        continue
                        
            # Check if there are remaining subgoals
            result = await self.get_proof_state()
            if "no more subgoals" in result.message.lower():
                # Complete proof
                result = await self.coq.send_command("Qed.")
                return result.parsed
            else:
                # Abort incomplete proof
                await self.coq.send_command("Abort.")
                return {
                    "status": "error", 
                    "message": "Could not complete proof automatically"
                }
            
        except Exception as e:
            logger.error(f"Proof error: {e}")
            await self.coq.send_command("Abort.")  # Clean up
            return {"status": "error", "message": str(e)}
            
    async def get_proof_state(self) -> Dict:
        """Get current proof state and goals"""
        try:
            result = await self.coq.send_command("Show.")
            return result.parsed
        except Exception as e:
            logger.error(f"Get proof state error: {e}")
            return {"status": "error", "message": str(e)}