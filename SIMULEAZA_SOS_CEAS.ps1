$ErrorActionPreference = "Stop"

Write-Host "[SIMULATOR CEAS] Trimit semnalul Bluetooth / mDNS catre AI Dispatcher..." -ForegroundColor Cyan

$body = @{
    type = "VOICE_SOS"
    payload = @{
        location = "44.4268, 26.1025"
        transcription = "Am cazut in casa, va rog ajutor! Nu ma pot ridica."
        heartRate = 120
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/dispatch" -Method Post -Body $body -ContentType "application/json"

Write-Host "`n[RĂSPUNS DE LA SERVERUL AI]:" -ForegroundColor Green
$response | ConvertTo-Json | Write-Host
