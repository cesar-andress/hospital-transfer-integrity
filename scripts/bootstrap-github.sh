#!/usr/bin/env bash
# Create labels, milestones, and issues. Requires a PAT with repo scope:
#   gh auth login   # or GH_TOKEN with public_repo / repo
set -euo pipefail
REPO="${REPO:-cesar-andress/hospital-transfer-integrity}"

echo "Bootstrapping $REPO …"

create_label() {
  local name=$1 color=$2 desc=$3
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null \
    || gh label edit "$name" --repo "$REPO" --color "$color" --description "$desc"
}

create_label "track:saas" "0E8A16" "Daniel transfer SaaS"
create_label "track:api" "1D4ED8" "Alessa IVS"
create_label "track:joint" "7C3AED" "Both students"
create_label "boundary" "B91C1C" "Architecture / contract wall"
create_label "mvp" "EA580C" "December MVP"
create_label "ambitious" "DB2777" "Ambitious roadmap item"

ms_mvp=$(gh api "repos/$REPO/milestones" -f title='MVP, December 2026' \
  -f description='Joint demo-able vertical slice. Due 2026-12-19.' \
  -f due_on='2026-12-19T23:59:59Z' --jq .number)
ms_depth=$(gh api "repos/$REPO/milestones" -f title='Depth, February 2027' \
  -f description='Security + clinical depth. Due 2027-02-27.' \
  -f due_on='2027-02-27T23:59:59Z' --jq .number)
ms_done=$(gh api "repos/$REPO/milestones" -f title='Complete, May 2027' \
  -f description='Thesis-ready. Due 2027-05-15.' \
  -f due_on='2027-05-15T23:59:59Z' --jq .number)

echo "Milestones: MVP=$ms_mvp Depth=$ms_depth Complete=$ms_done"
echo "Create issues from docs/project/ISSUES.md (titles/bodies) and assign after invites."
echo "Project board suggested title: Hospital Transfer and Integrity MVP"
