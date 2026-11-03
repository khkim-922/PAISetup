# DRM 감긴 문서에서 글자를 뽑는다 — Fasoo 에이전트가 도는 PC 의 오피스를 태워서.
#
# 왜 이 파일이 있나: Fasoo DRM 은 파일을 통째로 자기 컨테이너로 감싼다. 머리 바이트가
# `%PDF-`·`PK` 가 아니게 되므로 어떤 파서(PDFium·pdfplumber·python-docx·openpyxl)도
# 형식 인식 단계에서 죽는다. 정식 오피스 앱은 그 보호를 복호해 주므로 그것을 태운다.
#
# 규모가 이 파일을 정당화한다 — 문서가 여러 건이고 확장자가 갈리고, 앱 인스턴스를
# 재사용해야 느려지지 않는다. 한 건이면 이 파일 없이 인라인으로 해도 된다.
#
# 이 파일은 본체다 — 인자 · 대상 모으기 · 화면 · `-OutDir` 출력 · 끝 정리 · 종료 값. 읽는 함수(띄우기 · Job ·
# `Read-With*` · 글 밖 셈)는 `office-read.ps1` 이 들고, 제 꼴로 내는 앱은 그 부품을 점 소싱해 제 본체를 쓴다.

[CmdletBinding()]
param(
    # 읽을 파일들. 폴더를 주면 그 안의 지원 확장자를 전부 훑는다.
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$Path,

    # 뽑은 글자를 넣을 폴더. 생략하면 화면으로만 낸다.
    [string]$OutDir,

    # 화면에 낼 때 파일마다 보여줄 앞부분 글자 수.
    [int]$Preview = 300
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot 'office-session.ps1')
. (Join-Path $PSScriptRoot 'office-read.ps1')
# 파워포인트는 하나만 뜬다 — 띄우기 전에 사람이 쓰고 있었는지 New-OfficeApp 이 여기 적어, 끝에서 그 앱을 안 끈다
$PptWasRunning = $false

# 부품이 센 「글 밖」의 영어 열쇠 → 화면의 한국어. 파워포인트는 그림과 도형을 안 갈라 하나로 센다
$VISUAL_WORD = @{ tables = '표'; images = '그림'; shapes = '도형'; formulas = '수식'; charts = '차트'; fields = '필드' }
$VISUAL_WORD_PPT = @{ images = '그림·도형' }

# 센 것을 한 줄로 — 0 이면 빈 글이다(부를 것이 없다)
function Format-Visual {
    param([hashtable]$Counts, [string]$AppName)
    if (-not $Counts -or $Counts.Count -eq 0) { return '' }
    $words = @{}
    foreach ($key in $Counts.Keys) {
        $word = if ($AppName -eq 'PPT' -and $VISUAL_WORD_PPT.ContainsKey($key)) { $VISUAL_WORD_PPT[$key] } else { $VISUAL_WORD[$key] }
        if (-not $word) { $word = $key }
        $words[$word] = $Counts[$key]
    }
    return ' · 글 밖 ' + (($words.Keys | Sort-Object | ForEach-Object { "$_ $($words[$_])" }) -join ' · ')
}

# ── 대상 모으기 ────────────────────────────────────────────────────────────
$targets = [System.Collections.Generic.List[string]]::new()
foreach ($item in $Path) {
    if (Test-Path -LiteralPath $item -PathType Container) {
        Get-ChildItem -LiteralPath $item -File | Where-Object {
            $HANDLER.ContainsKey($_.Extension.ToLower())
        } | ForEach-Object { $targets.Add($_.FullName) }
    } elseif (Test-Path -LiteralPath $item) {
        $targets.Add((Resolve-Path -LiteralPath $item).Path)
    } else {
        Write-Warning "없는 경로: $item"
    }
}
if ($targets.Count -eq 0) { Write-Error '읽을 파일이 없다.'; exit 1 }

if ($OutDir -and -not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

# ── 앱별로 묶어 돈다 — 앱 생성이 비싸므로 확장자별로 모아 한 번만 띄운다 ──────
$byApp = $targets | Group-Object { $HANDLER[[System.IO.Path]::GetExtension($_).ToLower()] }
$apps = @{}
$spawnedPids = @{}                     # 이 판이 띄운 PID → 앱 이름
$officeJob = New-OfficeJob
$done = 0
$failed = 0

try {
    foreach ($group in $byApp) {
        $appName = $group.Name
        if (-not $appName) { continue }

        if (-not $apps.ContainsKey($appName)) {
            try {
                $apps[$appName] = New-OfficeApp -AppName $appName -SpawnedPids ([ref]$spawnedPids) -Job $officeJob
            } catch {
                Write-Warning "$appName 를 못 띄웠다: $($_.Exception.Message)"
                $failed += $group.Count
                continue
            }
        }
        $app = $apps[$appName]

        foreach ($file in $group.Group) {
            $name = [System.IO.Path]::GetFileName($file)
            $head = Get-FileHead -LiteralPath $file
            $wrapped = -not (Test-PlainFormat -LiteralPath $file)
            $mark = if ($wrapped) { 'DRM' } else { '평문' }

            try {
                $read = switch ($appName) {
                    'Word'  { Read-WithWord  -App $app -LiteralPath $file }
                    'Excel' { Read-WithExcel -App $app -LiteralPath $file }
                    'PPT'   { Read-WithPPT   -App $app -LiteralPath $file }
                }
                $text = [string]$read.Text
                $len = $text.Length
                Write-Output "[$mark] $name — $appName · 글자 $len$(Format-Visual -Counts $read.Visual -AppName $appName) · 머리 [$head]"

                if ($OutDir) {
                    $dest = Join-Path $OutDir "$name.txt"
                    $text | Out-File -LiteralPath $dest -Encoding utf8
                } elseif ($Preview -gt 0 -and $len -gt 0) {
                    $cut = $text.Substring(0, [Math]::Min($Preview, $len)) -replace '\s+', ' '
                    Write-Output "    $cut"
                }
                $done++
            } catch {
                # 실패를 삼키지 않는다 — 어느 파일이 왜 안 됐는지가 다음 판단의 근거다.
                Write-Output "[$mark] $name — 실패($appName): $($_.Exception.Message)"
                $failed++
            }
        }
    }
} finally {
    # ⚠ 여기를 건너뛰면 보이지 않는 오피스 프로세스가 쌓여 다음 실행이 느려지거나 멈춘다.
    #   다만 사람이 쓰던 앱(문서가 남았거나, 원래 떠 있던 파워포인트)은 끄지 않는다(office-session.ps1)
    $quitOf = @{}                      # 앱마다 Exit-OfficeApp 이 끝냈나 — 거짓이면 문서가 남아(또는 못 세어) 살려 둔 것
    foreach ($kind in @($apps.Keys)) {
        $was = ($kind -eq 'PPT') -and $PptWasRunning
        $quitOf[$kind] = [bool](Exit-OfficeApp -App $apps[$kind] -Kind $kind -WasRunning $was)
    }
    $keptAlive = ($quitOf.Values -contains $false)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    # ⚠ 파워포인트는 COM Quit 후에도 Fasoo DRM 훅이나 잔여 핸들 때문에 프로세스가 남아
    # "열람 권한이 없습니다(0x703000...)" 팝업이 무한 반복될 수 있다 — 이 판이 띄운 파워포인트가 Quit 뒤에도 남았으면 강제로
    # 끝낸다(그 앱만). Quit 을 안 한 판(발표가 남았거나 못 셌다)은 안 끝낸다 — 파워포인트는 하나만 떠서, 판이 도는 몇 초 사이
    # 사람이 연 발표가 이 인스턴스로 들어와 있을 수 있고 강제로 끝내면 저장 안 한 채 닫힌다. 그때 남는 것은 팝업이지 사람의 발표가
    # 아니다. 워드 · 엑셀은 Quit 으로 끝난다 — 같은 까닭으로 강제로 끝내지 않는다.
    if ($quitOf['PPT']) {
        foreach ($entry in @($spawnedPids.GetEnumerator())) {
            if ($entry.Value -ne 'PPT') { continue }
            if (Get-Process -Id $entry.Key -ErrorAction SilentlyContinue) { Stop-Process -Id $entry.Key -Force -ErrorAction SilentlyContinue }
        }
    }
    # 정상으로 끝나는 판에서 Job 손잡이를 닫기 전에 끝내기 규칙을 끈다 — 살려 둔 앱이 있으면 그 문서가 같이 닫힌다.
    # 살려 둔 것이 없으면 켠 채 닫아 Quit 뒤에도 남은 것을 거둔다. 끊긴 판은 여기 안 닿으니 Job 이 그대로 끝낸다.
    if ($officeJob -ne [IntPtr]::Zero) {
        if ($keptAlive) { [void](Set-OfficeJobKill -Job $officeJob -On $false) }
        [void][DrmRead.Job]::CloseHandle($officeJob)
    }

    # ⚠ DocumentRecovery 트리를 통째로 지우면 사용자의 정상적인 미저장 복구 파일이 날아간다.
    # $targets 에 매칭되는 특정 항목만 선별 삭제(Targeted Cleanup)한다.
    $targetLeaves = @($targets | ForEach-Object { Split-Path -Path $_ -Leaf })
    $officeVerKeys = @(Get-ChildItem -Path "HKCU:\Software\Microsoft\Office" -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d+\.\d+$' })
    foreach ($ver in $officeVerKeys) {
        foreach ($appKey in @('PowerPoint', 'Word', 'Excel')) {
            $recPath = "HKCU:\Software\Microsoft\Office\$($ver.PSChildName)\$appKey\Resiliency\DocumentRecovery"
            if (Test-Path -LiteralPath $recPath) {
                try {
                    $item = Get-Item -LiteralPath $recPath -ErrorAction SilentlyContinue
                    if ($item) {
                        foreach ($valName in $item.GetValueNames()) {
                            $isMatch = $false
                            foreach ($tl in $targetLeaves) {
                                if ($valName -like "*$tl*") { $isMatch = $true; break }
                            }
                            if (-not $isMatch) {
                                try {
                                    $rawBytes = [byte[]]$item.GetValue($valName)
                                    $rawText = [System.Text.Encoding]::Unicode.GetString($rawBytes)
                                    foreach ($tl in $targetLeaves) {
                                        if ($rawText -like "*$tl*") { $isMatch = $true; break }
                                    }
                                } catch { }
                            }
                            if ($isMatch) {
                                Remove-ItemProperty -LiteralPath $recPath -Name $valName -Force -ErrorAction SilentlyContinue
                            }
                        }
                    }
                } catch { }
            }
        }
    }

    # 읽기 과정에서 생성된 임시 락 파일(~$...) 정리
    foreach ($target in $targets) {
        $parentDir = Split-Path -Path $target -Parent
        $fileName = Split-Path -Path $target -Leaf
        $lockFile = Join-Path $parentDir ("~$" + $fileName)
        if (Test-Path -LiteralPath $lockFile) {
            Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Output ''
Write-Output "읽음 $done · 실패 $failed · 전체 $($targets.Count)"
if ($OutDir) { Write-Output "글자는 여기 — $OutDir" }
if ($failed -gt 0) { exit 1 }
