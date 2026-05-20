param(
    [string]$Message = ""
)

if (-not $Message) {
    $Message = "Sync changes $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

$changes = git status --short
if (-not $changes) {
    Write-Output "No local changes to commit. Pushing current branch to origin/master..."
    git push origin master
    exit $LASTEXITCODE
}

Write-Output "Staging all changes..."
git add -A

Write-Output "Committing with message: $Message"
git commit -m "$Message"

Write-Output "Pushing to origin/master..."
git push origin master
exit $LASTEXITCODE
