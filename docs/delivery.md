# Git handoff

The local repository started without commits or a remote. The existing GitHub main branch contains commit e0a43e3b7051ee18117b76330c7d255b51228616. Implementation is committed locally; pushing is intentionally stopped because remote history is absent locally.

Review remote history first:

```powershell
git remote -v
git fetch origin
git log --oneline --graph --all
git diff --stat main origin/main
```

Do not push until the histories have been reconciled and reviewed. One option after review is to merge the remote history into local main; this can produce conflicts and must be handled deliberately:

```powershell
git merge origin/main --allow-unrelated-histories
# Resolve any conflicts and complete the merge before continuing.
.\.venv\Scripts\python.exe -m pytest -q
git status
git push -u origin main
```

Never force-push. If authentication is unavailable, authenticate Git with your GitHub account using your normal credential manager and retry the ordinary push only after review.
