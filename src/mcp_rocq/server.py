"""
MCP Server for Coq Integration
Provides advanced logical reasoning capabilities through Coq
"""
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Any, List, Dict

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .handlers.coq_session import CoqSession
from .handlers.type_checker import TypeChecker
from .handlers.inductive_types import InductiveTypeHandler
from .handlers.prover import ProofHandler

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mcp_rocq')

class RoCQServer(Server):
    def __init__(self, coq_path: Path, lib_path: Path):
        super().__init__("rocq")
        
        # Initialize Coq session
        self.coq = CoqSession(coq_path, lib_path)
        
        # Initialize handlers
        self.type_checker = TypeChecker(self.coq)
        self.inductive_handler = InductiveTypeHandler(self.coq)
        self.proof_handler = ProofHandler(self.coq)

    async def cleanup(self):
        """Clean up resources"""
        if self.coq:
            await self.coq.close()
        await super().cleanup()

async def main(coq_path: Path, lib_path: Path):
    """Start the RoCQ server"""
    logger.info(f"Starting RoCQ Server with Coq at: {coq_path}")

    server = RoCQServer(coq_path, lib_path)

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="type_check",
                description="Check type of a term with optional expected type", 
                inputSchema={
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "Term to type check"
                        },
                        "expected_type": {
                            "type": "string",
                            "description": "Optional expected type"
                        },
                        "context": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of modules to import"
                        }
                    },
                    "required": ["term"]
                }
            ),
            types.Tool(
                name="define_inductive",
                description="Define and verify an inductive type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the inductive type"
                        },
                        "constructors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of constructor definitions"
                        },
                        "verify": {
                            "type": "boolean",
                            "description": "Whether to verify key properties",
                            "default": False
                        }
                    },
                    "required": ["name", "constructors"]
                }
            ),
            types.Tool(
                name="prove_property",
                description="Prove a logical property",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "property_stmt": {
                            "type": "string",
                            "description": "Property to prove"
                        },
                        "tactics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of tactics to apply"
                        },
                        "use_automation": {
                            "type": "boolean",
                            "description": "Whether to try automated proving",
                            "default": True
                        }
                    },
                    "required": ["property_stmt"]
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str,
                             arguments: dict[str, Any] | None
                             ) -> list[types.TextContent | types.ImageContent]:
        """Handle tool execution requests"""
        try:
            if name == "type_check":
                result = await server.type_checker.check_type(
                    term=arguments["term"],
                    expected_type=arguments.get("expected_type"),
                    context=arguments.get("context")
                )
                return [types.TextContent(type="text", text=str(result))]

            elif name == "define_inductive":
                result = await server.inductive_handler.define_inductive(
                    name=arguments["name"],
                    constructors=arguments["constructors"],
                    verify=arguments.get("verify", False)
                )
                return [types.TextContent(type="text", text=str(result))]

            elif name == "prove_property":
                result = await server.proof_handler.prove_property(
                    property_stmt=arguments["property_stmt"],
                    tactics=arguments.get("tactics"),
                    use_automation=arguments.get("use_automation", True)
                )
                return [types.TextContent(type="text", text=str(result))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Tool error: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rocq",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )

def cli():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='MCP RoCQ Server')
    parser.add_argument('--coq-path', type=str,
                      default="F:/Coq-Platform~8.19~2024.10/bin/coqtop.exe",
                      help='Path to coqtop executable')
    parser.add_argument('--lib-path', type=str,
                      default="F:/Coq-Platform~8.19~2024.10/lib/coq",
                      help='Path to Coq library directory')
    args = parser.parse_args()

    try:
        asyncio.run(main(Path(args.coq_path), Path(args.lib_path)))
    except KeyboardInterrupt:
        logger.info("Server stopped")

if __name__ == "__main__":
    cli()