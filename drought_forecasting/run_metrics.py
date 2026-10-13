import sys
import os

# Ensure the module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agriminds.ml.ablation import get_ablation_suite

def main():
    suite = get_ablation_suite()
    metrics = suite.get_ablation_summary()
    
    print("\n=======================================================")
    print("      AI-DREWS SCIENTIFIC ABLATION METRICS")
    print("=======================================================\n")
    
    for m in metrics:
        print(f"[{m['name']}] ({m['model_key']})")
        print(f"  Description:   {m['description']}")
        print(f"  ROC-AUC:       {m['roc_auc']}")
        print(f"  PR-AUC:        {m['pr_auc']}")
        print(f"  Brier Score:   {m['brier_score']} (Lower is better)")
        print(f"  Skill Gain:    +{m['skill_gain_vs_local_pct']}% improvement vs Local Baseline")
        print("-" * 55)

if __name__ == "__main__":
    main()
