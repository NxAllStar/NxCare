#!/usr/bin/env bash
# remind-push.sh
# Event: Stop   Matcher: *
# Non-blocking reminder. At session end, if the current branch is a task branch
# (feat/|fix/|chore/|refactor/|docs/|test/ + TASK-) with commit(s) not yet on its remote, remind the
# user to push and open a PR when the flow is green - and never merge their own PR. Silent otherwise.
# Always exit 0 so it NEVER blocks the stop. It only prints a message; it never runs git write ops.

# Only meaningful inside a git work tree.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Only nag on task branches (naming from git-workflow.md). Never on main/other/detached HEAD.
case "$branch" in
  feat/TASK-*|fix/TASK-*|chore/TASK-*|refactor/TASK-*|docs/TASK-*|test/TASK-*) : ;;
  *) exit 0 ;;
esac

# Commits on this branch not yet on its upstream. No upstream => never pushed; compare to
# origin/main (or local main) so a brand-new branch still counts its commits as unpushed.
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
if [ -n "$upstream" ]; then
  ahead=$(git rev-list --count "${upstream}..HEAD" 2>/dev/null)
  hint="push (git push)"
else
  base="origin/main"
  git rev-parse --verify "$base" >/dev/null 2>&1 || base="main"
  ahead=$(git rev-list --count "${base}..HEAD" 2>/dev/null)
  hint="push it (git push -u origin ${branch})"
fi

# Silent unless there is actually something unpushed.
[ -n "$ahead" ] && [ "$ahead" -gt 0 ] 2>/dev/null || exit 0

printf 'Reminder: %s commit(s) on %s are not on the remote yet. When the feature flow is green (tests + code/security review + /secret-scan), %s and open a PR. Do NOT merge your own PR - another person reviews and merges (git-workflow.md).\n' \
  "$ahead" "$branch" "$hint" >&2

exit 0
