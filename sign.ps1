# Signs dist\MyNote.exe with a self-signed code-signing certificate.
#
# What this does and doesn't do:
#  - Replaces "Unknown Publisher" with your own name in the UAC/SmartScreen
#    prompt, and makes the exe tamper-evident (any edit after signing breaks
#    the signature).
#  - Does NOT by itself stop SmartScreen warnings for anyone else -- a
#    self-signed cert is only trusted on machines where it's been explicitly
#    imported (see the instructions this script prints at the end). Real,
#    warning-free trust for strangers requires a CA-issued certificate,
#    which needs identity verification and typically costs money.
#
# Uses only what's already built into Windows (PowerShell's own
# New-SelfSignedCertificate / Set-AuthenticodeSignature) -- no separate
# Windows SDK / signtool.exe install needed.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$exePath = "dist\MyNote.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "dist\MyNote.exe not found -- run build.bat first." -ForegroundColor Red
    exit 1
}

$certSubject = "CN=MyNote (self-signed)"
$existing = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
    Where-Object { $_.Subject -eq $certSubject }

if ($existing) {
    $cert = $existing[0]
    Write-Host "Reusing existing signing certificate (expires $($cert.NotAfter))."
} else {
    Write-Host "Creating a new self-signed code-signing certificate..."
    $cert = New-SelfSignedCertificate `
        -Subject $certSubject `
        -Type CodeSigningCert `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyUsage DigitalSignature `
        -FriendlyName "MyNote self-signed" `
        -NotAfter (Get-Date).AddYears(5)
}

Write-Host "Signing $exePath ..."
$result = Set-AuthenticodeSignature -FilePath $exePath -Certificate $cert `
    -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm SHA256

if ($result.Status -ne "Valid") {
    Write-Host "Signing finished with status: $($result.Status) -- $($result.StatusMessage)" -ForegroundColor Yellow
} else {
    Write-Host "Signed successfully." -ForegroundColor Green
}

$certOutPath = "MyNote-signing-cert.cer"
Export-Certificate -Cert $cert -FilePath $certOutPath | Out-Null

Write-Host ""
Write-Host "Exported the public certificate to $certOutPath."
Write-Host ""
Write-Host "To stop SmartScreen from flagging MyNote.exe as an unknown" -ForegroundColor Cyan
Write-Host "publisher ON THIS PC, open an ADMIN PowerShell window (right-click" -ForegroundColor Cyan
Write-Host "Start > Windows PowerShell (Admin), approve the UAC prompt yourself)" -ForegroundColor Cyan
Write-Host "and run:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Import-Certificate -FilePath `"$PSScriptRoot\$certOutPath`" -CertStoreLocation Cert:\LocalMachine\Root" -ForegroundColor White
Write-Host "  Import-Certificate -FilePath `"$PSScriptRoot\$certOutPath`" -CertStoreLocation Cert:\LocalMachine\TrustedPublisher" -ForegroundColor White
Write-Host ""
Write-Host "To do the same on another PC, copy $certOutPath there first, then run those two commands on that machine." -ForegroundColor Cyan
