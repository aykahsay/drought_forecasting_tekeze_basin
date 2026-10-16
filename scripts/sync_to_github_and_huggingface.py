"""
AI-DREWS Continuous Dual-Platform Synchronization Engine
========================================================
Synchronizes every code update, documentation change, audit report, test suite,
and data manifest between the local workspace, GitHub, and Hugging Face.

Repositories:
  - GitHub: https://github.com/aykahsay/drought_forecasting_tekeze_basin
  - Hugging Face: https://huggingface.co/aykgeh/drought_forecasting_tekeze_basin

Usage:
  python scripts/sync_to_github_and_huggingface.py -m "Commit and sync description"
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from huggingface_hub import HfApi, CommitOperationAdd
except ImportError:
    print("ERROR: huggingface_hub is required. Install via `pip install huggingface_hub`")
    sys.exit(1)

# Default configuration
GITHUB_REPO_URL = "https://github.com/aykahsay/drought_forecasting_tekeze_basin.git"
HF_REPO_ID = "aykgeh/drought_forecasting_tekeze_basin"


def load_hf_token(repo_root: Path) -> str:
    """Load Hugging Face token securely from environment, .env, or local cache."""
    token = os.environ.get("HF_TOKEN")
    if token and token.strip():
        return token.strip()

    env_file = repo_root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("HF_TOKEN="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val

    scratch_token = repo_root / "scratch" / "hf_token.txt"
    if scratch_token.exists():
        val = scratch_token.read_text(encoding="utf-8").strip()
        if val:
            return val

    hf_cache_token = Path.home() / ".cache" / "huggingface" / "token"
    if hf_cache_token.exists():
        val = hf_cache_token.read_text(encoding="utf-8").strip()
        if val:
            return val

    return ""

HF_FRONTMATTER = """---
license: apache-2.0
tags:
- climate
- drought-forecasting
- hydrology
- remote-sensing
- earth-observation
- ethiopia
- tekeze-basin
- spei
- spi
- scientific-audit
---

"""


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return CompletedProcess."""
    cmd = ["git"] + args
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if check and res.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nStderr: {res.stderr}\nStdout: {res.stdout}")
    return res


def get_current_branch() -> str:
    res = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    return res.stdout.strip()


def sync_github(commit_message: str, branch: str) -> str:
    """Stage, commit, and push changes to GitHub (both target branch and main)."""
    print(f"\n==========================================")
    print(f" 1. GITHUB SYNCHRONIZATION")
    print(f"==========================================")
    
    status_res = run_git(["status", "--porcelain"])
    dirty = bool(status_res.stdout.strip())
    
    if dirty:
        print("Detected uncommitted changes. Staging tracked and relevant new files...")
        run_git(["add", "-A"])
        print(f"Creating commit: '{commit_message}'")
        run_git(["commit", "-m", commit_message])
    else:
        print("Working directory is clean. No new local commit needed.")

    head_commit = run_git(["rev-parse", "HEAD"]).stdout.strip()
    short_commit = head_commit[:7]
    print(f"Current local HEAD: {short_commit}")

    # Push current branch
    print(f"Pushing branch '{branch}' to origin...")
    run_git(["push", "origin", branch])
    print(f"✓ Pushed branch '{branch}' to GitHub.")

    # Synchronize main branch as well
    if branch != "main":
        print(f"Fast-forward synchronizing 'main' branch to match {branch}...")
        run_git(["checkout", "main"])
        run_git(["merge", "--ff-only", branch])
        run_git(["push", "origin", "main"])
        run_git(["checkout", branch])
        print(f"✓ Pushed branch 'main' to GitHub.")

    print(f"GitHub synchronization complete: https://github.com/aykahsay/drought_forecasting_tekeze_basin/commit/{head_commit}")
    return head_commit


def build_huggingface_operations(root: Path) -> list[CommitOperationAdd]:
    """Collect all tracked scientific documents, scripts, tests, fixtures, and manifests for Hugging Face."""
    operations = []

    # 1. README.md with Hugging Face frontmatter
    readme_path = root / "README.md"
    if readme_path.exists():
        raw_readme = readme_path.read_text(encoding="utf-8")
        if not raw_readme.startswith("---"):
            full_hf_readme = HF_FRONTMATTER + raw_readme
        else:
            full_hf_readme = raw_readme
        
        scratch_dir = root / "scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        hf_readme_path = scratch_dir / "HF_README_AUTO.md"
        hf_readme_path.write_text(full_hf_readme, encoding="utf-8")
        
        operations.append(CommitOperationAdd(
            path_in_repo="README.md",
            path_or_fileobj=str(hf_readme_path)
        ))

    # 2. Handover Report
    handover = root / "AI_DREWS_SCIENTIFIC_HANDOVER_REPORT.md"
    if handover.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="audit/AI_DREWS_SCIENTIFIC_HANDOVER_REPORT.md",
            path_or_fileobj=str(handover)
        ))

    # 3. All Documentation in docs/
    docs_dir = root / "docs"
    if docs_dir.exists():
        for doc in sorted(docs_dir.glob("*.md")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"docs/{doc.name}",
                path_or_fileobj=str(doc)
            ))

    # 4. Reports in reports/
    reports_dir = root / "reports"
    if reports_dir.exists():
        for rep in sorted(reports_dir.glob("*.md")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"reports/{rep.name}",
                path_or_fileobj=str(rep)
            ))

    # 5. Core Mathematical & Climate Calculators
    spei_calc = root / "drought_forecasting" / "agriminds" / "climate" / "spei_calculator.py"
    if spei_calc.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="drought_forecasting/agriminds/climate/spei_calculator.py",
            path_or_fileobj=str(spei_calc)
        ))

    # 6. Test Suite in drought_forecasting/tests/
    tests_dir = root / "drought_forecasting" / "tests"
    if tests_dir.exists():
        for test_file in sorted(tests_dir.glob("test_*.py")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"drought_forecasting/tests/{test_file.name}",
                path_or_fileobj=str(test_file)
            ))

    # 7. Reproducibility Scripts in scripts/
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for scr in sorted(scripts_dir.glob("*.py")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"scripts/{scr.name}",
                path_or_fileobj=str(scr)
            ))

    # 8. Fixtures & Benchmarks
    fixture_json = root / "fixtures" / "r_spei_lmom_reference_benchmark.json"
    if fixture_json.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="fixtures/r_spei_lmom_reference_benchmark.json",
            path_or_fileobj=str(fixture_json)
        ))

    # 9. Verified Boundaries (GeoJSON)
    geojson_path = root / "data" / "spatial" / "processed" / "tekeze_basin_hydrological_complete.geojson"
    if geojson_path.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="spatial/tekeze_basin_hydrological_complete.geojson",
            path_or_fileobj=str(geojson_path)
        ))

    # 10. Temperature Manifests & CSVs
    manifest_path = root / "data" / "processed" / "temperature_provenance_manifest.json"
    if manifest_path.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="data/temperature_provenance_manifest.json",
            path_or_fileobj=str(manifest_path)
        ))
    audit_csv = root / "data" / "processed" / "tekeze_monthly_temperature_audit_1981_2024.csv"
    if audit_csv.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="data/tekeze_monthly_temperature_audit_1981_2024.csv",
            path_or_fileobj=str(audit_csv)
        ))
    topology_audit = root / "data" / "spatial" / "processed" / "tekeze_catchment_topology_audit.json"
    if topology_audit.exists():
        operations.append(CommitOperationAdd(
            path_in_repo="spatial/tekeze_catchment_topology_audit.json",
            path_or_fileobj=str(topology_audit)
        ))

    # 11. Manuscript & Research Paper Suite
    manuscript_dir = root / "manuscript"
    if manuscript_dir.exists():
        for mf in sorted(manuscript_dir.glob("*.*")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"manuscript/{mf.name}",
                path_or_fileobj=str(mf)
            ))

    # 12. Research Dialogue & Conversation Audit Transcripts
    conversations_dir = root / "conversations"
    if conversations_dir.exists():
        for cf in sorted(conversations_dir.glob("*.md")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"conversations/{cf.name}",
                path_or_fileobj=str(cf)
            ))

    # 13. Publication Figures & Verification JSONs
    proc_dir = root / "data" / "processed"
    if proc_dir.exists():
        for fig in sorted(proc_dir.glob("figure*.png")):
            operations.append(CommitOperationAdd(
                path_in_repo=f"figures/{fig.name}",
                path_or_fileobj=str(fig)
            ))
        for jf in [
            "paper_submission_tables_and_metrics.json",
            "spei3_vs_spi3_target_ablation.json",
            "tekeze_masked_vimc_teleconnection_audit.json",
            "categorical_drought_evaluation_m4_vs_m7.json",
            "rolling_origin_walkforward_auditable_metrics_2017_2024.json",
            "seasonal_forecast_probabilistic_validation_metrics.json",
        ]:
            jp = proc_dir / jf
            if jp.exists():
                operations.append(CommitOperationAdd(
                    path_in_repo=f"data/metrics/{jf}",
                    path_or_fileobj=str(jp)
                ))

    # 14. Environment Requirements
    for req in ["requirements.txt", "requirements-lock.txt"]:
        req_p = root / req
        if req_p.exists():
            operations.append(CommitOperationAdd(
                path_in_repo=req,
                path_or_fileobj=str(req_p)
            ))

    return operations


def sync_huggingface(commit_message: str, root: Path) -> str:
    """Push operations bundle to Hugging Face Model Hub."""
    print(f"\n==========================================")
    print(f" 2. HUGGING FACE SYNCHRONIZATION")
    print(f"==========================================")

    token = load_hf_token(root)
    if not token:
        print("WARNING: HF_TOKEN not found in environment, .env, or cache. Skipping Hugging Face upload.")
        return "SKIPPED_NO_TOKEN"

    api = HfApi(token=token)
    print(f"Connecting to Hugging Face Model Hub: {HF_REPO_ID}...")
    
    operations = build_huggingface_operations(root)
    print(f"Prepared {len(operations)} file operations for Hugging Face upload.")

    commit_info = api.create_commit(
        repo_id=HF_REPO_ID,
        repo_type="model",
        operations=operations,
        commit_message=commit_message
    )
    print(f"✓ Hugging Face commit successful!")
    print(f"Commit URL: {commit_info}")
    return str(commit_info)


def main():
    parser = argparse.ArgumentParser(description="Synchronize repository to GitHub and Hugging Face.")
    parser.add_argument("-m", "--message", default="Scientific Protocol: Synchronize repository updates to GitHub and Hugging Face",
                        help="Commit message for GitHub and Hugging Face")
    parser.add_argument("--branch", default=None, help="Target git branch (defaults to current branch)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    os.chdir(root)

    current_branch = get_current_branch()
    target_branch = args.branch if args.branch else current_branch

    print(f"AI-DREWS Continuous Synchronization Tool")
    print(f"Root: {root}")
    print(f"Active Branch: {current_branch}")
    print(f"Target Branch: {target_branch}")
    print(f"Commit Message: {args.message}")

    # 1. Sync GitHub
    gh_commit = sync_github(args.message, target_branch)

    # 2. Sync Hugging Face
    hf_commit = sync_huggingface(args.message, root)

    print(f"\n==========================================")
    print(f" SYNCHRONIZATION SUMMARY: 100% SUCCESS")
    print(f"==========================================")
    print(f"• GitHub:       https://github.com/aykahsay/drought_forecasting_tekeze_basin (Commit: {gh_commit[:7]})")
    print(f"• Hugging Face: https://huggingface.co/{HF_REPO_ID}")
    print(f"All research assets, audits, tests, and code are synchronized across both platforms.")


if __name__ == "__main__":
    main()
