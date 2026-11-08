param(
    [Parameter(Mandatory = $true)][string]$Conf,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$root = Split-Path -Parent $PSScriptRoot
$toolHome = Join-Path $root "tools\dl-learner\dllearner-1.5.0"
$launcher = Join-Path $toolHome "bin\cli.bat"
$javaHome = if ($env:DLLEARNER_JAVA_HOME) { $env:DLLEARNER_JAVA_HOME } else { "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot" }

if (-not (Test-Path $launcher)) { throw "DL-Learner not found at $launcher" }
if (-not (Test-Path (Join-Path $javaHome "bin\java.exe"))) { throw "java.exe not found under $javaHome" }

$confPath = (Resolve-Path $Conf).Path

$env:JAVA_HOME = $javaHome
$env:PATH = "$javaHome\bin;$env:PATH"
$env:JAVA_OPTS = "--add-opens java.base/java.lang.invoke=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED"

Push-Location $toolHome
try {
    & $launcher $confPath @ExtraArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
