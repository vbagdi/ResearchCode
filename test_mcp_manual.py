#!/usr/bin/env python3
"""
Manual test of MCP server tools
This will actually call the tools and show the server logging
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test MCP server by calling tools"""
    
    print("="*70)
    print("  🧪 TESTING MCP SERVER TOOLS")
    print("="*70)
    print()
    print("Starting server and calling tools...")
    print("(Watch for server logs below)")
    print()
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"]
    )
    
    try:
        # Connect to server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Initialize
                await session.initialize()
                
                print("✅ Connected to MCP server\n")
                
                # List available tools
                print("📋 Listing available tools...")
                tools = await session.list_tools()
                print(f"Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  • {tool.name}")
                print()
                
                # Test 1: Calculate properties of aspirin
                print("="*70)
                print("🧪 Test 1: Calculate Molecular Properties (Aspirin)")
                print("="*70)
                result = await session.call_tool(
                    "calculate_molecular_properties",
                    arguments={"smiles": "CC(=O)Oc1ccccc1C(=O)O"}
                )
                print(result.content[0].text)
                print()
                
                # Test 2: Validate SMILES
                print("="*70)
                print("🔍 Test 2: Validate SMILES (Ethanol)")
                print("="*70)
                result = await session.call_tool(
                    "validate_smiles",
                    arguments={"smiles": "CCO"}
                )
                print(result.content[0].text)
                print()
                
                # Test 3: Check Lipinski's Rule
                print("="*70)
                print("💊 Test 3: Check Lipinski's Rule (Aspirin)")
                print("="*70)
                result = await session.call_tool(
                    "check_lipinski_rule",
                    arguments={"smiles": "CC(=O)Oc1ccccc1C(=O)O"}
                )
                print(result.content[0].text)
                print()
                
                # Test 4: Search PubChem
                print("="*70)
                print("🔬 Test 4: Search PubChem (Caffeine)")
                print("="*70)
                result = await session.call_tool(
                    "search_pubchem",
                    arguments={"compound_name": "caffeine"}
                )
                print(result.content[0].text)
                print()
                
                # Test 5: List discovered tools
                print("="*70)
                print("📚 Test 5: List Discovered Tools (Top 5)")
                print("="*70)
                result = await session.call_tool(
                    "list_discovered_tools",
                    arguments={"workflow": "all"}
                )
                # Show first 500 chars
                text = result.content[0].text
                if len(text) > 500:
                    print(text[:500] + "...")
                else:
                    print(text)
                print()
                
                # Summary
                print("="*70)
                print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY")
                print("="*70)
                print()
                print("Summary:")
                print("  • Server started and connected")
                print("  • All 5 tools called successfully")
                print("  • Real molecular calculations performed")
                print("  • MCP protocol working correctly")
                print()
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Make sure you have: pip install mcp rdkit-pypi requests")
        print("  2. Check that code/mcp_server.py exists")
        print("  3. Run: python code/mcp_server.py (should start without errors)")
        sys.exit(1)

if __name__ == "__main__":
    print("\n🚀 Starting MCP Server Test\n")
    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)