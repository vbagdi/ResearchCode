"""
Automated Chemistry Tool Discovery Pipeline
Finds Python tools for computational chemistry/drug discovery
"""

import requests
import time
import json
from typing import List, Dict
from datetime import datetime
import re

class ChemToolDiscovery:
    
    def __init__(self):
        self.pypi_base = "https://pypi.org/pypi"
        self.github_api = "https://api.github.com"
        self.github_token = None
        self.discovered_tools = []
        
    def get_pypi_info(self, package_name: str) -> Dict:
        """Get detailed info from PyPI JSON API"""
        try:
            url = f"{self.pypi_base}/{package_name}/json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                info = data['info']
                
                return {
                    'name': package_name,
                    'source': 'pypi',
                    'description': info.get('summary', ''),
                    'version': info.get('version', ''),
                    'author': info.get('author', ''),
                    'home_page': info.get('home_page', ''),
                    'pypi_url': f"https://pypi.org/project/{package_name}",
                    'keywords': info.get('keywords', ''),
                }
        except Exception as e:
            pass
        
        return None
    
    def search_github(self, topics: List[str], min_stars: int = 10) -> List[Dict]:
        """Search GitHub for chemistry tool repositories"""
        print(f"\n🔍 Searching GitHub with {len(topics)} topics...")
        tools = []
        seen_repos = set()
        
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        for topic in topics:
            print(f"  Searching topic: '{topic}'")
            try:
                url = f"{self.github_api}/search/repositories"
                params = {
                    'q': f'topic:{topic} language:python stars:>{min_stars}',
                    'sort': 'stars',
                    'per_page': 30
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"    Found {results['total_count']} repositories")
                    
                    for repo in results.get('items', [])[:30]:
                        repo_name = repo['full_name']
                        
                        if repo_name not in seen_repos:
                            seen_repos.add(repo_name)
                            
                            tool = {
                                'name': repo['name'],
                                'source': 'github',
                                'github_url': repo['html_url'],
                                'description': repo.get('description', ''),
                                'stars': repo['stargazers_count'],
                                'forks': repo['forks_count'],
                                'language': repo.get('language', ''),
                                'topics': repo.get('topics', []),
                                'updated_at': repo['updated_at'],
                                'created_at': repo['created_at'],
                            }
                            
                            updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
                            tool['days_since_update'] = (datetime.now(updated.tzinfo) - updated).days
                            
                            tools.append(tool)
                    
                elif response.status_code == 403:
                    print(f"    ⚠️  Rate limited. Waiting 60 seconds...")
                    time.sleep(60)
                else:
                    print(f"    Error: Status {response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"    Error searching GitHub for '{topic}': {e}")
                continue
        
        print(f"  Total unique repos found: {len(tools)}")
        return tools
    
    def enrich_github_with_pypi(self, tools: List[Dict]) -> List[Dict]:
        """Check if GitHub tools have PyPI packages"""
        print(f"\n🔗 Enriching GitHub tools with PyPI data...")
        
        for i, tool in enumerate(tools):
            if tool['source'] == 'github':
                package_name = tool['name'].lower().replace('_', '-')
                
                pypi_info = self.get_pypi_info(package_name)
                if pypi_info:
                    tool['has_pypi'] = True
                    tool['pypi_url'] = pypi_info['pypi_url']
                    print(f"  ✓ Found PyPI: {package_name}")
                else:
                    tool['has_pypi'] = False
                
                if i % 10 == 0 and i > 0:
                    print(f"  Processed {i}/{len(tools)} tools...")
                    time.sleep(1)
        
        return tools
    
    def calculate_quality_score(self, tool: Dict) -> float:
        """Calculate quality score based on multiple signals"""
        score = 0.0
        
        if 'stars' in tool:
            stars = tool['stars']
            if stars > 1000:
                score += 10
            elif stars > 500:
                score += 8
            elif stars > 100:
                score += 6
            elif stars > 50:
                score += 4
            else:
                score += 2
        
        if 'days_since_update' in tool:
            days = tool['days_since_update']
            if days < 90:
                score += 5
            elif days < 180:
                score += 3
            elif days < 365:
                score += 1
        
        desc = tool.get('description') or ''
        desc = desc.lower()
        name = tool.get('name', '').lower()
        
        chem_keywords = [
            'chem', 'molecule', 'drug', 'compound', 'smiles',
            'protein', 'docking', 'descriptor', 'pharma', 'medicinal',
            'rdkit', 'molecular', 'crystal', 'reaction'
        ]
        
        keyword_matches = sum(1 for kw in chem_keywords if kw in desc or kw in name)
        score += min(keyword_matches * 2, 10)
        
        if tool.get('has_pypi', False):
            score += 3
        
        if 'topics' in tool and len(tool['topics']) > 2:
            score += 2
        
        # Bonus for foundation tools
        if tool.get('source') == 'pypi' and 'foundation-tool' in tool.get('topics', []):
            score += 5
        
        return round(score, 2)
    
    def categorize_by_workflow(self, tools: List[Dict]) -> Dict[str, List[str]]:
        """Categorize tools by scientific workflow"""
        print(f"\n📊 Categorizing tools by workflow...")
        
        workflows = {
            'virtual_screening': {
                'keywords': ['dock', 'screen', 'virtual', 'binding', 'score'],
                'tools': []
            },
            'property_prediction': {
                'keywords': ['predict', 'qsar', 'admet', 'property', 'descriptor', 'ml', 'machine'],
                'tools': []
            },
            'similarity_search': {
                'keywords': ['similar', 'search', 'fingerprint', 'compare', 'cluster'],
                'tools': []
            },
            'molecule_generation': {
                'keywords': ['generate', 'design', 'novo', 'synthesis', 'retro'],
                'tools': []
            },
            'visualization': {
                'keywords': ['visual', 'view', 'render', 'display', 'plot', 'draw'],
                'tools': []
            },
            'io_conversion': {
                'keywords': ['convert', 'format', 'read', 'write', 'parse', 'babel'],
                'tools': []
            },
            'simulation': {
                'keywords': ['dynamics', 'simulation', 'md', 'trajectory', 'force'],
                'tools': []
            },
            'database_access': {
                'keywords': ['database', 'pubchem', 'chembl', 'api', 'query'],
                'tools': []
            }
        }
        
        for tool in tools:
            desc = ((tool.get('description') or '') + ' ' + (tool.get('name') or '')).lower()
            
            for workflow_name, workflow_data in workflows.items():
                if any(kw in desc for kw in workflow_data['keywords']):
                    workflows[workflow_name]['tools'].append(tool['name'])
        
        print("\n  Workflow distribution:")
        for workflow_name, workflow_data in workflows.items():
            count = len(workflow_data['tools'])
            print(f"    {workflow_name}: {count} tools")
        
        return workflows
    
    def deduplicate(self, tools: List[Dict]) -> List[Dict]:
        """Remove duplicate tools"""
        seen_names = set()
        unique_tools = []
        
        for tool in tools:
            name = tool['name'].lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_tools.append(tool)
        
        return unique_tools
    
    def run_discovery(self, output_file: str = 'data/discovered_tools.json'):
        """Main discovery pipeline"""
        print("="*60)
        print("🧪 Chemistry Tool Discovery Pipeline")
        print("="*60)
        
        github_topics = [
            'cheminformatics',
            'drug-discovery',
            'computational-chemistry',
            'molecular-modeling',
            'medicinal-chemistry',
            'chemical-informatics'
        ]
        
        # Search GitHub
        github_tools = self.search_github(github_topics, min_stars=10)
        github_tools = self.enrich_github_with_pypi(github_tools)
        
        # Add foundation tools from PyPI
        print("\n🔍 Adding known foundation tools from PyPI...")
        foundation_tools = [
            'rdkit-pypi', 'rdkit', 'openbabel-wheel', 'openbabel',
            'biopython', 'prody', 'mordred', 'chempy', 
            'pymol-open-source', 'biotite'
        ]
        
        existing_names = {t['name'].lower().replace('-', '').replace('_', '') for t in github_tools}
        
        for pkg_name in foundation_tools:
            normalized = pkg_name.lower().replace('-', '').replace('_', '')
            
            if normalized not in existing_names:
                info = self.get_pypi_info(pkg_name)
                if info:
                    info['has_pypi'] = True
                    info['stars'] = 0
                    info['days_since_update'] = 30
                    info['topics'] = ['foundation-tool']
                    github_tools.append(info)
                    print(f"  ✓ Added: {pkg_name}")
                    existing_names.add(normalized)
                else:
                    print(f"  ✗ Not found: {pkg_name}")
        
        all_tools = self.deduplicate(github_tools)
        
        print(f"\n📦 Total unique tools found: {len(all_tools)}")
        
        print(f"\n⚡ Calculating quality scores...")
        for tool in all_tools:
            tool['quality_score'] = self.calculate_quality_score(tool)
        
        all_tools.sort(key=lambda x: x['quality_score'], reverse=True)
        
        workflows = self.categorize_by_workflow(all_tools)
        
        print(f"\n💾 Saving results to {output_file}...")
        
        output_data = {
            'metadata': {
                'total_tools': len(all_tools),
                'timestamp': datetime.now().isoformat(),
                'sources': ['github', 'pypi'],
                'topics_searched': github_topics,
                'foundation_tools_added': foundation_tools
            },
            'tools': all_tools,
            'workflows': workflows
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Saved {len(all_tools)} tools")
        
        print(f"\n🏆 Top 10 Tools by Quality Score:")
        print(f"{'Rank':<6}{'Tool':<25}{'Score':<8}{'Stars':<8}{'Updated'}")
        print("-"*60)
        for i, tool in enumerate(all_tools[:10], 1):
            days_ago = tool.get('days_since_update', 'N/A')
            print(f"{i:<6}{tool['name'][:24]:<25}{tool['quality_score']:<8}{tool.get('stars', 'N/A'):<8}{days_ago}")
        
        print("\n" + "="*60)
        print("✅ Discovery Complete!")
        print("="*60)
        
        return all_tools


def main():
    """Run the discovery pipeline"""
    import os
    
    os.makedirs('data', exist_ok=True)
    
    discoverer = ChemToolDiscovery()
    tools = discoverer.run_discovery('data/discovered_tools.json')
    
    print(f"\n📊 Summary:")
    print(f"  Total tools discovered: {len(tools)}")
    print(f"  Output: data/discovered_tools.json")
    print(f"\n🚀 Next steps:")
    print(f"  1. Run validation: python code/validate.py")
    print(f"  2. Build MCP server with top tools")


if __name__ == "__main__":
    main()