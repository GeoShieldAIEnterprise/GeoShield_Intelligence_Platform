$base = "http://127.0.0.1:8000"
$candidates = @(
    "/",
    "/dashboard",
    "/api",
    "/api/docs",
    "/docs",
    "/openapi.json",
    "/api/predict",
    "/api/predictions",
    "/api/status",
    "/api/health",
    "/api/imagery",
    "/api/satellite",
    "/api/events",
    "/api/disasters"
)

foreach ($path in $candidates) {
    try {
        $resp = Invoke-WebRequest -Uri "$base$path" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "=== $path -> $($resp.StatusCode) ===" -ForegroundColor Green
        Write-Host $resp.Content.Substring(0, [Math]::Min(500, $resp.Content.Length))
        Write-Host ""
    } catch {
        Write-Host "=== $path -> FAILED: $($_.Exception.Message) ===" -ForegroundColor DarkGray
    }
}
