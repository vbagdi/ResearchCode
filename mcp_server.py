#!/usr/bin/env python3
"""
MCP Server for Chemistry Tool Discovery
Exposes top chemistry tools via Model Context Protocol
"""

import json
import sys
import asyncio
from typing import Any, Sequence
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Try importing chemistry libraries
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("Warning: RDKit not available. Install with: pip install rdkit-pypi", file=sys.stderr)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available. Install with: pip install requests", file=sys.stderr)


def log(message):
    """Log messages to stderr so they don't interfere with MCP protocol"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


class ChemistryMCPServer:
    """MCP Server exposing chemistry tools"""
    
    def __init__(self):
        self.server = Server("chemistry-tools")
        self.call_count = 0
        log("🧪 Initializing Chemistry MCP Server...")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register tool handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available chemistry tools"""
            log("📋 Client requested tool list")
            tools = []
            
            # Tool 1: Calculate molecular properties
            if RDKIT_AVAILABLE:
                tools.append(Tool(
                    name="calculate_molecular_properties",
                    description="Calculate molecular properties (MW, LogP, H-bond donors/acceptors) from SMILES",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "smiles": {
                                "type": "string",
                                "description": "SMILES string representation of molecule"
                            }
                        },
                        "required": ["smiles"]
                    }
                ))
            
            # Tool 2: Validate SMILES
            if RDKIT_AVAILABLE:
                tools.append(Tool(
                    name="validate_smiles",
                    description="Check if a SMILES string is valid",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "smiles": {
                                "type": "string",
                                "description": "SMILES string to validate"
                            }
                        },
                        "required": ["smiles"]
                    }
                ))
            
            # Tool 3: Search PubChem
            if REQUESTS_AVAILABLE:
                tools.append(Tool(
                    name="search_pubchem",
                    description="Search PubChem database for compound information by name",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "compound_name": {
                                "type": "string",
                                "description": "Name of the compound to search"
                            }
                        },
                        "required": ["compound_name"]
                    }
                ))
            
            # Tool 4: Check Lipinski's Rule of Five
            if RDKIT_AVAILABLE:
                tools.append(Tool(
                    name="check_lipinski_rule",
                    description="Check if molecule passes Lipinski's Rule of Five for drug-likeness",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "smiles": {
                                "type": "string",
                                "description": "SMILES string of molecule"
                            }
                        },
                        "required": ["smiles"]
                    }
                ))
            
            # Tool 5: List discovered tools
            tools.append(Tool(
                name="list_discovered_tools",
                description="List all 115 chemistry tools discovered by the automated system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "string",
                            "description": "Optional: Filter by workflow (virtual_screening, property_prediction, similarity_search, molecule_generation, visualization, io_conversion, simulation, database_access)",
                            "enum": ["all", "virtual_screening", "property_prediction", "similarity_search", 
                                   "molecule_generation", "visualization", "io_conversion", "simulation", "database_access"]
                        }
                    }
                }
            ))
            
            log(f"✓ Returning {len(tools)} available tools")
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Execute tool"""
            self.call_count += 1
            log(f"🔧 Tool call #{self.call_count}: {name}")
            log(f"   Arguments: {arguments}")
            
            try:
                # Tool 1: Calculate molecular properties
                if name == "calculate_molecular_properties":
                    if not RDKIT_AVAILABLE:
                        log("   ✗ RDKit not available")
                        return [TextContent(type="text", text="Error: RDKit not installed. Run: pip install rdkit-pypi")]
                    
                    smiles = arguments.get("smiles")
                    log(f"   → Calculating properties for: {smiles}")
                    mol = Chem.MolFromSmiles(smiles)
                    
                    if mol is None:
                        log(f"   ✗ Invalid SMILES: {smiles}")
                        return [TextContent(type="text", text=f"Error: Invalid SMILES string: {smiles}")]
                    
                    properties = {
                        "molecular_weight": round(Descriptors.MolWt(mol), 2),
                        "logP": round(Crippen.MolLogP(mol), 2),
                        "h_bond_donors": Descriptors.NumHDonors(mol),
                        "h_bond_acceptors": Descriptors.NumHAcceptors(mol),
                        "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
                        "aromatic_rings": Descriptors.NumAromaticRings(mol)
                    }
                    
                    log(f"   ✓ MW: {properties['molecular_weight']}, LogP: {properties['logP']}")
                    
                    result = f"Molecular Properties for {smiles}:\n"
                    result += f"  Molecular Weight: {properties['molecular_weight']} g/mol\n"
                    result += f"  LogP: {properties['logP']}\n"
                    result += f"  H-Bond Donors: {properties['h_bond_donors']}\n"
                    result += f"  H-Bond Acceptors: {properties['h_bond_acceptors']}\n"
                    result += f"  Rotatable Bonds: {properties['rotatable_bonds']}\n"
                    result += f"  Aromatic Rings: {properties['aromatic_rings']}"
                    
                    return [TextContent(type="text", text=result)]
                
                # Tool 2: Validate SMILES
                elif name == "validate_smiles":
                    if not RDKIT_AVAILABLE:
                        log("   ✗ RDKit not available")
                        return [TextContent(type="text", text="Error: RDKit not installed")]
                    
                    smiles = arguments.get("smiles")
                    log(f"   → Validating SMILES: {smiles}")
                    mol = Chem.MolFromSmiles(smiles)
                    
                    if mol is None:
                        log(f"   ✗ Invalid SMILES")
                        return [TextContent(type="text", text=f"Invalid SMILES: {smiles}")]
                    else:
                        canonical = Chem.MolToSmiles(mol)
                        log(f"   ✓ Valid! Canonical: {canonical}")
                        return [TextContent(type="text", text=f"Valid SMILES\nCanonical form: {canonical}")]
                
                # Tool 3: Search PubChem
                elif name == "search_pubchem":
                    if not REQUESTS_AVAILABLE:
                        log("   ✗ Requests library not available")
                        return [TextContent(type="text", text="Error: requests library not installed")]
                    
                    compound_name = arguments.get("compound_name")
                    log(f"   → Searching PubChem for: {compound_name}")
                    
                    search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES/JSON"
                    
                    try:
                        response = requests.get(search_url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            props = data['PropertyTable']['Properties'][0]
                            log(f"   ✓ Found CID: {props['CID']}")
                            
                            result = f"PubChem results for '{compound_name}':\n"
                            result += f"  CID: {props['CID']}\n"
                            result += f"  Molecular Formula: {props.get('MolecularFormula', 'N/A')}\n"
                            result += f"  Molecular Weight: {props.get('MolecularWeight', 'N/A')} g/mol\n"
                            result += f"  SMILES: {props.get('CanonicalSMILES', 'N/A')}"
                            
                            return [TextContent(type="text", text=result)]
                        else:
                            log(f"   ✗ Not found (status {response.status_code})")
                            return [TextContent(type="text", text=f"No results found for '{compound_name}'")]
                    except Exception as e:
                        log(f"   ✗ Error: {str(e)}")
                        return [TextContent(type="text", text=f"Error searching PubChem: {str(e)}")]
                
                # Tool 4: Check Lipinski's Rule
                elif name == "check_lipinski_rule":
                    if not RDKIT_AVAILABLE:
                        log("   ✗ RDKit not available")
                        return [TextContent(type="text", text="Error: RDKit not installed")]
                    
                    smiles = arguments.get("smiles")
                    log(f"   → Checking Lipinski's Rule for: {smiles}")
                    mol = Chem.MolFromSmiles(smiles)
                    
                    if mol is None:
                        log(f"   ✗ Invalid SMILES")
                        return [TextContent(type="text", text=f"Error: Invalid SMILES: {smiles}")]
                    
                    mw = Descriptors.MolWt(mol)
                    logp = Crippen.MolLogP(mol)
                    hbd = Descriptors.NumHDonors(mol)
                    hba = Descriptors.NumHAcceptors(mol)
                    
                    violations = 0
                    issues = []
                    
                    if mw > 500:
                        violations += 1
                        issues.append(f"MW > 500 ({mw:.1f})")
                    if logp > 5:
                        violations += 1
                        issues.append(f"LogP > 5 ({logp:.1f})")
                    if hbd > 5:
                        violations += 1
                        issues.append(f"H-bond donors > 5 ({hbd})")
                    if hba > 10:
                        violations += 1
                        issues.append(f"H-bond acceptors > 10 ({hba})")
                    
                    if violations == 0:
                        log(f"   ✓ PASSES Lipinski's Rule (0 violations)")
                    else:
                        log(f"   ✗ FAILS Lipinski's Rule ({violations} violations)")
                    
                    result = f"Lipinski's Rule of Five for {smiles}:\n"
                    result += f"  Molecular Weight: {mw:.1f} g/mol (≤500)\n"
                    result += f"  LogP: {logp:.1f} (≤5)\n"
                    result += f"  H-bond Donors: {hbd} (≤5)\n"
                    result += f"  H-bond Acceptors: {hba} (≤10)\n\n"
                    
                    if violations == 0:
                        result += "✓ PASSES Lipinski's Rule (0 violations)\nLikely drug-like compound"
                    else:
                        result += f"✗ FAILS Lipinski's Rule ({violations} violation(s))\n"
                        result += "Issues: " + ", ".join(issues)
                    
                    return [TextContent(type="text", text=result)]
                
                # Tool 5: List discovered tools
                elif name == "list_discovered_tools":
                    workflow = arguments.get("workflow", "all")
                    log(f"   → Listing tools for workflow: {workflow}")
                    
                    try:
                        with open("data/discovered_tools.json", "r") as f:
                            data = json.load(f)
                        
                        tools_list = data.get("tools", [])
                        total = len(tools_list)
                        log(f"   ✓ Loaded {total} tools from database")
                        
                        if workflow != "all":
                            # Filter by workflow
                            workflow_tools = data.get("workflows", {}).get(workflow, {}).get("tools", [])
                            filtered = [t for t in tools_list if t["name"] in workflow_tools]
                            log(f"   ✓ Filtered to {len(filtered)} tools for {workflow}")
                            
                            result = f"Tools for workflow '{workflow}' ({len(filtered)} tools):\n\n"
                            for i, tool in enumerate(filtered[:10], 1):
                                result += f"{i}. {tool['name']}\n"
                                result += f"   Score: {tool.get('quality_score', 'N/A')}\n"
                                result += f"   {tool.get('description', 'No description')[:80]}...\n\n"
                            
                            if len(filtered) > 10:
                                result += f"\n... and {len(filtered) - 10} more tools in this workflow"
                        else:
                            result = f"Discovered Chemistry Tools (Total: {total})\n\n"
                            result += "Top 10 by Quality Score:\n\n"
                            
                            for i, tool in enumerate(tools_list[:10], 1):
                                result += f"{i}. {tool['name']} (Score: {tool.get('quality_score', 'N/A')})\n"
                                result += f"   Stars: {tool.get('stars', 'N/A')} | "
                                result += f"Updated: {tool.get('days_since_update', 'N/A')} days ago\n"
                                result += f"   {tool.get('description', 'No description')[:80]}...\n\n"
                            
                            result += f"\nWorkflows:\n"
                            for wf_name, wf_data in data.get("workflows", {}).items():
                                result += f"  • {wf_name}: {len(wf_data.get('tools', []))} tools\n"
                        
                        return [TextContent(type="text", text=result)]
                    
                    except FileNotFoundError:
                        log("   ✗ discovered_tools.json not found")
                        return [TextContent(type="text", text="Error: discovered_tools.json not found. Run discover.py first.")]
                    except Exception as e:
                        log(f"   ✗ Error loading tools: {str(e)}")
                        return [TextContent(type="text", text=f"Error loading tools: {str(e)}")]
                
                else:
                    log(f"   ✗ Unknown tool: {name}")
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
            except Exception as e:
                log(f"   ✗ Exception: {str(e)}")
                return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        log("🚀 Starting MCP server on stdio...")
        log(f"   RDKit available: {RDKIT_AVAILABLE}")
        log(f"   Requests available: {REQUESTS_AVAILABLE}")
        log("   Server ready and waiting for connections...")
        log("   (Press Ctrl+C to stop)")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = ChemistryMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        log("\n👋 Server shutting down...")
    except Exception as e:
        log(f"\n❌ Server error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())