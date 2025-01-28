"""
Entry point for MCP RoCQ server
"""
import asyncio
import argparse
from pathlib import Path
from .server import serve

def run():
    parser = argparse.ArgumentParser(description='MCP RoCQ Server')
    parser.add_argument('--coq-path', type=str,
                    # example "F:/Coq-Platform~8.19~2024.10/bin/coqtop.exe",
                      help='Path to coqtop executable')
    parser.add_argument('--lib-path', type=str,
                    # example "F:/Coq-Platform~8.19~2024.10/lib/coq", 
                      help='Path to Coq library directory')
    
    args = parser.parse_args()
    asyncio.run(serve(Path(args.coq_path), Path(args.lib_path)))

if __name__ == '__main__':
    run()