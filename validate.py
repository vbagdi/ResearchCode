"""
Validation: Compare discovered tools against gold standard
"""

import json
from typing import List, Dict, Set

def load_gold_standard() -> List[str]:
    """Load gold standard tools"""
    try:
        with open('data/gold_standard.json', 'r') as f:
            data = json.load(f)
            return data['gold_standard_tools']
    except FileNotFoundError:
        print("⚠️  Warning: gold_standard.json not found. Using default.")
        return [
            "rdkit", "openbabel", "deepchem", "pubchempy", "mordred",
            "chempy", "mdanalysis", "pymol-open-source", "prody", "biopython"
        ]

def load_discovered_tools() -> List[Dict]:
    """Load discovered tools"""
    with open('data/discovered_tools.json', 'r') as f:
        data = json.load(f)
        return data['tools']

def normalize_name(name: str) -> str:
    """Normalize tool name for comparison"""
    return name.lower().replace('-', '').replace('_', '').replace(' ', '')

def calculate_metrics(discovered: List[Dict], gold_standard: List[str]) -> Dict:
    """Calculate precision, recall, and other metrics"""
    
    # Normalize names
    discovered_names = {normalize_name(t['name']) for t in discovered}
    gold_names = {normalize_name(name) for name in gold_standard}
    
    # Top 20 discovered tools
    top_20_names = {normalize_name(t['name']) for t in discovered[:20]}
    
    # Calculate metrics
    found_in_gold = discovered_names & gold_names
    found_in_top20 = top_20_names & gold_names
    
    recall = len(found_in_gold) / len(gold_names) if gold_names else 0
    precision_at_20 = len(found_in_top20) / 20 if len(top_20_names) >= 20 else 0
    
    # Find what was missed
    missed = gold_names - discovered_names
    
    # Find novel discoveries (in top 20 but not in gold standard)
    novel_in_top20 = top_20_names - gold_names
    
    return {
        'total_discovered': len(discovered),
        'gold_standard_size': len(gold_standard),
        'found_count': len(found_in_gold),
        'recall': round(recall, 3),
        'precision_at_20': round(precision_at_20, 3),
        'missed_tools': list(missed),
        'found_tools': list(found_in_gold),
        'novel_top20': list(novel_in_top20)
    }

def print_report(metrics: Dict, discovered: List[Dict]):
    """Print validation report"""
    
    print("="*70)
    print("📊 VALIDATION REPORT")
    print("="*70)
    
    print(f"\n📦 Discovery Summary:")
    print(f"  Total tools discovered: {metrics['total_discovered']}")
    print(f"  Gold standard size: {metrics['gold_standard_size']}")
    
    print(f"\n✅ Performance Metrics:")
    print(f"  Recall: {metrics['recall']:.1%} ({metrics['found_count']}/{metrics['gold_standard_size']} gold standard tools found)")
    print(f"  Precision@20: {metrics['precision_at_20']:.1%} ({int(metrics['precision_at_20']*20)}/20 top results are gold standard)")
    
    if metrics['found_tools']:
        print(f"\n🎯 Found Gold Standard Tools ({len(metrics['found_tools'])}):")
        for tool in sorted(metrics['found_tools']):
            # Find the actual tool object for score
            matching = [t for t in discovered if normalize_name(t['name']) == tool]
            if matching:
                score = matching[0]['quality_score']
                stars = matching[0].get('stars', 'N/A')
                print(f"  ✓ {tool:20s} (score: {score}, stars: {stars})")
    
    if metrics['missed_tools']:
        print(f"\n❌ Missed Gold Standard Tools ({len(metrics['missed_tools'])}):")
        for tool in sorted(metrics['missed_tools']):
            print(f"  ✗ {tool}")
    
    if metrics['novel_top20']:
        print(f"\n🆕 Novel High-Quality Discoveries in Top 20 ({len(metrics['novel_top20'])}):")
        for norm_name in list(metrics['novel_top20'])[:10]:
            # Find the actual tool
            matching = [t for t in discovered[:20] if normalize_name(t['name']) == norm_name]
            if matching:
                tool = matching[0]
                print(f"  • {tool['name']:20s} (score: {tool['quality_score']}, stars: {tool.get('stars', 'N/A')})")
    
    print(f"\n💡 Analysis:")
    if metrics['recall'] >= 0.8:
        print(f"  ✅ EXCELLENT: High recall ({metrics['recall']:.1%}) - finding most important tools")
    elif metrics['recall'] >= 0.6:
        print(f"  ⚠️  GOOD: Moderate recall ({metrics['recall']:.1%}) - missing some key tools")
    else:
        print(f"  ❌ NEEDS WORK: Low recall ({metrics['recall']:.1%}) - missing many key tools")
    
    if metrics['precision_at_20'] >= 0.8:
        print(f"  ✅ EXCELLENT: High precision@20 ({metrics['precision_at_20']:.1%}) - top results are high quality")
    elif metrics['precision_at_20'] >= 0.5:
        print(f"  ⚠️  GOOD: Moderate precision@20 ({metrics['precision_at_20']:.1%})")
    else:
        print(f"  ❌ NEEDS WORK: Low precision@20 ({metrics['precision_at_20']:.1%})")
    
    print("\n" + "="*70)

def save_results(metrics: Dict):
    """Save validation results"""
    output_file = 'results/validation_metrics.json'
    
    import os
    os.makedirs('results', exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n💾 Saved validation metrics to {output_file}")

def main():
    """Run validation"""
    print("\n🔍 Loading data...")
    
    gold_standard = load_gold_standard()
    discovered = load_discovered_tools()
    
    print(f"  Gold standard: {len(gold_standard)} tools")
    print(f"  Discovered: {len(discovered)} tools")
    
    print("\n⚡ Calculating metrics...")
    metrics = calculate_metrics(discovered, gold_standard)
    
    print_report(metrics, discovered)
    save_results(metrics)
    
    print("\n🚀 Next steps:")
    print("  1. Review missed tools - why weren't they found?")
    print("  2. Examine novel discoveries - are they actually good?")
    print("  3. Build MCP server with top tools")

if __name__ == "__main__":
    main()