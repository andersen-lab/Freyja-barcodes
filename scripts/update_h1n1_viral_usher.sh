#!/usr/bin/env bash
# Build Freyja barcodes for the H1N1_viral_usher_HA group from the public
# viral_usher tree for Influenza A virus (A/California/07/2009(H1N1)), HA segment:
# https://github.com/AngieHinrichs/viral_usher_trees/tree/main/trees/Influenza_A_virus_A_California_07_2009_H1N1_4
#
# Mirrors .github/workflows/pull.yml layout: H1N1_viral_usher_HA/<date>/ plus H1N1_viral_usher_HA/latest/.
# All inputs are public; no GitHub token is needed.
#
# Usage: scripts/update_h1n1_viral_usher.sh [--no-git]
#   --no-git   build and write files only; do not pull/commit/push
#
# Environment overrides:
#   FREYJA_ENV   conda/micromamba env prefix containing freyja + matUtils
#                (default: /home/josh/micromamba/envs/freyja)
#                Works with pandas 2, and with pandas 3 once Freyja includes the
#                pandas-3 fix (andersen-lab/Freyja PR #333; released Freyja <= 2.0.7
#                still needs pandas<3, or run with PYTHONPATH=<Freyja checkout>).
#   GROUP        output directory name (default: H1N1_viral_usher_HA)

set -euo pipefail

GROUP="${GROUP:-H1N1_viral_usher_HA}"
FREYJA_ENV="${FREYJA_ENV:-/home/josh/micromamba/envs/freyja}"
TREE=Influenza_A_virus_A_California_07_2009_H1N1_4
REF=treetime_rerooted_NC_026433.1.fa
BASE="https://raw.githubusercontent.com/AngieHinrichs/viral_usher_trees/main/trees/${TREE}"

DO_GIT=1
[[ "${1:-}" == "--no-git" ]] && DO_GIT=0

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${FREYJA_ENV}/bin:${PATH}"
command -v freyja >/dev/null || { echo "freyja not found in ${FREYJA_ENV}" >&2; exit 1; }
command -v matUtils >/dev/null || { echo "matUtils not found in ${FREYJA_ENV}" >&2; exit 1; }

# Prevent overlapping cron runs.
exec 9>"${REPO}/.update_${GROUP}.lock"
flock -n 9 || { echo "another run is in progress" >&2; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "[$(date -Is)] Downloading tree and reference for ${GROUP}"
curl -fsSL --retry 3 -o "${WORK}/optimized.pb.gz" "${BASE}/optimized.pb.gz"
curl -fsSL --retry 3 -o "${WORK}/tree_reference.fa" "${BASE}/${REF}"

# The tree reference is too divergent from modern H1N1 to align reads to, so express
# barcodes relative to CY121680.1 (same reference as H1N1/). See the python script.
cp "${REPO}/H1N1/latest/reference.fasta" "${WORK}/reference.fasta"
cd "$WORK"
matUtils extract -i optimized.pb.gz -C lineagePaths.txt >/dev/null
python "${REPO}/scripts/reroot_viral_usher_barcodes.py" lineagePaths.txt \
  "${WORK}/tree_reference.fa" "${WORK}/reference.fasta" "${WORK}/barcode"

cd "$REPO"
[[ -s "${WORK}/barcode.csv" ]] || { echo "empty barcode.csv" >&2; exit 1; }

# Skip if barcodes are unchanged from latest (the tree is rebuilt irregularly).
if [[ -f "${GROUP}/latest/barcode.csv" ]] && cmp -s "${WORK}/barcode.csv" "${GROUP}/latest/barcode.csv"; then
  echo "Barcodes unchanged; nothing to do."
  exit 0
fi

DATE="$(date +%Y-%m-%d)"
mkdir -p "${GROUP}/${DATE}" "${GROUP}/latest"
cp "${WORK}/barcode.csv" "${WORK}/barcode.feather" "${WORK}/reference.fasta" "${GROUP}/${DATE}/"
cp "${GROUP}/${DATE}"/* "${GROUP}/latest/"
echo "Wrote ${GROUP}/${DATE} and ${GROUP}/latest"

if (( DO_GIT )); then
  git pull --ff-only origin main
  git add "${GROUP}"
  git commit -m "Add pathogen barcodes for ${GROUP}" || echo "No changes to commit"
  git push origin main
fi
