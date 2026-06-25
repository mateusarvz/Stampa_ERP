param(
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'

$AppName = 'Stampa SaaS'
$AppFolderName = 'Stampa SaaS'
$AppDataFolderName = 'Stampa_SaaS'
$UserDataRoot = $env:LOCALAPPDATA
if (-not $UserDataRoot) {
    $UserDataRoot = $env:APPDATA
}
if (-not $UserDataRoot) {
    $UserDataRoot = [Environment]::GetFolderPath('LocalApplicationData')
}

$DataPath = Join-Path $UserDataRoot $AppDataFolderName
$InstallPaths = @(
    (Join-Path $env:ProgramFiles $AppFolderName)
    (Join-Path ${env:ProgramFiles(x86)} $AppFolderName)
    (Join-Path $env:LOCALAPPDATA $AppFolderName)
    (Join-Path $env:USERPROFILE '.venv_stampa')
)

function Write-Status([string]$Message) {
    if (-not $Silent) {
        Write-Host $Message
    }
}

function Remove-PathIfExists([string]$PathToRemove) {
    if ([string]::IsNullOrWhiteSpace($PathToRemove)) {
        return
    }

    if (Test-Path $PathToRemove) {
        Remove-Item -Path $PathToRemove -Recurse -Force
        Write-Status "Removido: $PathToRemove"
    }
}

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
        (Join-Path $env:ProgramFiles 'Stampa SaaS\unins000.exe')
        (Join-Path $env:ProgramFiles 'Stampa SaaS\unins001.exe')
        (Join-Path ${env:ProgramFiles(x86)} 'Stampa SaaS\unins000.exe')
        (Join-Path ${env:ProgramFiles(x86)} 'Stampa SaaS\unins001.exe')
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

Write-Status 'DesinstaladorGeral: iniciando remoção do Stampa SaaS...'

$Uninstaller = Get-StampaUninstaller
if ($Uninstaller) {
    Write-Status "Desinstalador encontrado: $Uninstaller"
    [void](Invoke-CommandLine $Uninstaller)
} else {
    Write-Status 'Desinstalador nao encontrado. Seguindo com limpeza local.'
}

Remove-PathIfExists $DataPath

foreach ($path in $InstallPaths) {
    Remove-PathIfExists $path
}

$ShortcutTargets = @(
    (Join-Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) 'Stampa SaaS.lnk')
    (Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Stampa SaaS.lnk')
    (Join-Path ([Environment]::GetFolderPath('CommonPrograms')) 'Stampa SaaS')
    (Join-Path ([Environment]::GetFolderPath('Programs')) 'Stampa SaaS')
)

foreach ($target in $ShortcutTargets) {
    Remove-PathIfExists $target
}

Write-Status 'Desinstalacao concluida.'