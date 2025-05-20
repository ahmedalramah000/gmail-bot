Write-Host "Setting up environment file with UTF-8 encoding..."
Get-Content -Path .\env_config.txt | Out-File -FilePath .\.env -Encoding utf8
Write-Host "Environment file has been set up successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run the bot with one of the following commands:"
Write-Host "python gmail_bot.py" -ForegroundColor Cyan
Write-Host "or"
Write-Host "python openai_code_forwarder.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 