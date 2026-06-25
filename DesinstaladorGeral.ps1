param(
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'

$AppName = 'Stampa SaaS'
$AppDataFolderName = 'Stampa_SaaS'
$UserDataRoot = $env:LOCALAPPDATA
if (-not $UserDataRoot) {
    $UserDataRoot = $env:APPDATA
}
if (-not $UserDataRoot) {
    $UserDataRoot = [Environment]::GetFolderPath('LocalApplicationData')
}

$DataPath = Join-Path $UserDataRoot $AppDataFolderName

function Get-UninstallEntries {
    $paths = @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            Get-ItemProperty $path -ErrorAction SilentlyContinue
        }
    }
}

function Get-StampaUninstaller {
    $candidates = Get-UninstallEntries | Where-Object {
        $_.DisplayName -match 'DesinstaladorGeral|Stampa SaaS|StampaSaaS'
    }

    $selected = $candidates | Sort-Object {
        if ($_.QuietUninstallString) { 0 } else { 1 }
    } | Select-Object -First 1

    if ($selected) {
        if ($selected.QuietUninstallString) {
            return $selected.QuietUninstallString
        }
        return $selected.UninstallString
    }

    $fallbacks = @(
        Join-Path ${env:ProgramFiles} 'Stampa SaaS\unins000.exe',
        Join-Path ${env:ProgramFiles} 'Stampa SaaS\unins001.exe',
        Join-Path ${env:ProgramFiles(x86)} 'Stampa SaaS\unins000.exe',
        Join-Path ${env:ProgramFiles(x86)} 'Stampa SaaS\unins001.exe'
    )

    foreach ($fallback in $fallbacks) {
        if ($fallback -and (Test-Path $fallback)) {
            return '"{0}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -f $fallback
        }
    }

    return $null
}

function Invoke-CommandLine([string]$CommandLine) {
    if (-not $CommandLine) {
        return $false
    }

    Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $CommandLine -Wait -NoNewWindow
    return $true
}

Write-Host 'DesinstaladorGeral: iniciando remoção do Stampa SaaS...'

$Uninstaller = Get-StampaUninstaller
if ($Uninstaller) {
    Write-Host "Desinstalador encontrado: $Uninstaller"
    [void](Invoke-CommandLine $Uninstaller)
} else {
    Write-Host 'Desinstalador nao encontrado. Seguindo com limpeza local.'
}

if (Test-Path $DataPath) {
    Remove-Item -Path $DataPath -Recurse -Force
    Write-Host "Removido: $DataPath"
}

$ShortcutTargets = @(
    Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) 'Stampa SaaS.lnk',
    Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Stampa SaaS.lnk',
    Join-Path ([Environment]::GetFolderPath('CommonPrograms')) 'Stampa SaaS',
    Join-Path ([Environment]::GetFolderPath('Programs')) 'Stampa SaaS'
)

foreach ($target in $ShortcutTargets) {
    if (Test-Path $target) {
        Remove-Item -Path $target -Recurse -Force
    }
}

Write-Host 'Desinstalacao concluida.'