<#
    drm-office-read 스크립트들이 함께 쓰는 오피스 세션 규칙 — 사람이 열어 둔 오피스와 문서는 건드리지 않는다.
    점 소싱으로 싣는다:  . (Join-Path $PSScriptRoot 'office-session.ps1')

    파워포인트는 사용자 하나에 하나만 뜨는 COM 서버라 New-Object 가 사람이 쓰는 파워포인트에 붙는다. 그대로
    Quit 하면 사람의 창과 저장 안 한 발표가 경고 없이 닫힌다. 같은 파일을 이미 열어 두었으면 Open 이 사람의
    문서 개체를 그대로 돌려준다 — 그것을 닫거나 Saved 를 찍으면 사람의 변경이 사라진다. 워드 · 엑셀은 보통 새
    인스턴스로 뜨지만 같은 규칙을 건다 — 붙은 자리였을 때 잃는 것이 사람의 문서라서다.
#>

function Open-OwnedDocument {
    <# $Open 으로 문서를 열고, 열기 전후 $Collection 의 수로 새로 연 것인지 가린다. 새로 열었으면 Owned 가 참 —
       사람이 이미 연 문서를 돌려받았으면 거짓이고, 그 문서에는 Saved 를 안 찍는다 #>
    param([ValidateSet('Word', 'Excel', 'PPT')][string]$Kind, $Collection, [scriptblock]$Open)
    $before = [int]$Collection.Count
    $doc = & $Open
    $owned = ([int]$Collection.Count -gt $before)
    if ($owned) { try { $doc.Saved = $true } catch { } }
    return [pscustomobject]@{ Kind = $Kind; Document = $doc; Owned = $owned }
}

function Close-OwnedDocument($Session) {
    <# 새로 연 문서만 저장하지 않고 닫는다. 사람의 문서는 COM 참조만 놓는다 #>
    if (-not $Session -or $null -eq $Session.Document) { return }
    if ($Session.Owned) {
        try { $Session.Document.Saved = $true } catch { }
        if ($Session.Kind -eq 'PPT') { try { $Session.Document.Close() } catch { } }      # 인자가 없다
        else { try { $Session.Document.Close($false) } catch { } }                        # SaveChanges=$false
    }
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Session.Document) } catch { }
    $Session.Document = $null
}

function Assert-WordPdfQuiet($App) {
    <# 워드로 PDF 를 열기 전에 부른다. 변환 안내창을 끄는 값이 없으면 숨은 워드가 그 창에 갇혀 멈춘다 —
       DisplayAlerts · ConfirmConversions 로는 그 창이 안 눌린다. 그 값은 사람이 PDF 를 열 때의 워드 동작도 바꾸므로
       스크립트가 심지 않고 알린다 #>
    $version = '16.0'
    try { $version = [string]$App.Version } catch { }
    $key = "HKCU:\Software\Microsoft\Office\$version\Word\Options"
    $value = $null
    try { $value = (Get-ItemProperty -LiteralPath $key -Name DisableConvertPdfWarning -ErrorAction Stop).DisableConvertPdfWarning } catch { }
    if ($value -ne 1) {
        throw ("이 PC 는 워드의 PDF 변환 안내창이 안 꺼져 있다 — 숨은 워드가 그 창에 갇혀 멈추므로 열지 않았다. " +
               "PAISetup 설치를 다시 돌리면(로그온 자동 실행도) 그 값을 1 로 둔다. 아니면 $key 의 DisableConvertPdfWarning 을 " +
               "1 로 두거나, 워드로 PDF 를 한 번 열어 「이 메시지를 다시 표시 안 함」을 체크한다.")
    }
}

function Assert-PdfConverted([string]$Head) {
    <# 워드가 PDF 를 변환 못 하고 파일 바이트를 날글로 읽으면 글자는 많은데 내용이 `%PDF-…` 다 — 성공으로 세지 않는다 #>
    if ($Head -and $Head.TrimStart().StartsWith('%PDF-')) {
        throw '워드가 PDF 를 변환하지 못하고 파일 바이트를 날글로 읽었다(%PDF-…) — 성공으로 세지 않는다.'
    }
}

function Test-RecoveryEntry {
    <# 복구 항목 하나(값 이름 · 값 바이트)가 $FileNames 의 파일 것인가 — 값 이름이나 값(UTF-16 글)에 그 파일 이름이 들었나로 가린다.
       글자 그대로 견준다 — 파일 이름의 「[ ]」 가 와일드카드로 읽히면 다른 파일의 항목이 걸린다 #>
    param([string]$EntryName, [byte[]]$EntryBytes, [string[]]$FileNames)
    $entryText = ''
    if ($EntryBytes) { try { $entryText = [System.Text.Encoding]::Unicode.GetString($EntryBytes) } catch { } }
    foreach ($fileName in $FileNames) {
        if (-not $fileName) { continue }
        if ($EntryName.IndexOf($fileName, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
        if ($entryText.IndexOf($fileName, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
    }
    return $false
}

function Clear-OwnedRecovery {
    <# 오피스가 죽으며 남긴 복구 항목(DocumentRecovery) 가운데 $Paths 의 파일 것만 지운다 — 남아 있으면 그 앱이 다음에 뜰 때 복구
       창이 먼저 떠 슬라이드쇼가 서지 않는다. 트리를 통째로 지우지 않는다 — 사람의 저장 안 한 복구 자료가 같은 자리에 있다.
       워드 · 엑셀 · 파워포인트의 모든 판을 훑고, 못 읽거나 못 지운 항목은 건너뛴다(던지지 않는다) #>
    param([string[]]$Paths = @())
    $ownedNames = @($Paths | Where-Object { $_ } | ForEach-Object { Split-Path -Path $_ -Leaf })
    if ($ownedNames.Count -eq 0) { return }
    $officeVersions = @(Get-ChildItem -Path 'HKCU:\Software\Microsoft\Office' -ErrorAction SilentlyContinue |
                        Where-Object { $_.PSChildName -match '^\d+\.\d+$' })
    foreach ($officeVersion in $officeVersions) {
        foreach ($appKey in @('PowerPoint', 'Word', 'Excel')) {
            $recoveryKey = "HKCU:\Software\Microsoft\Office\$($officeVersion.PSChildName)\$appKey\Resiliency\DocumentRecovery"
            if (-not (Test-Path -LiteralPath $recoveryKey)) { continue }
            try {
                $recoveryItem = Get-Item -LiteralPath $recoveryKey -ErrorAction SilentlyContinue
                if (-not $recoveryItem) { continue }
                foreach ($valueName in $recoveryItem.GetValueNames()) {
                    $valueBytes = $null
                    try { $valueBytes = [byte[]]$recoveryItem.GetValue($valueName) } catch { }
                    if (Test-RecoveryEntry -EntryName $valueName -EntryBytes $valueBytes -FileNames $ownedNames) {
                        Remove-ItemProperty -LiteralPath $recoveryKey -Name $valueName -Force -ErrorAction SilentlyContinue
                    }
                }
            } catch { }
        }
    }
}

function Exit-OfficeApp {
    <# 남은 문서가 없고 사람이 쓰던 파워포인트에 붙은 것이 아닐 때만 끈다. 끄지 않았으면 거짓을 돌려준다.
       문서가 남아 살려 두는 워드 · 엑셀은 보이게 해 둔다 — 숨긴 채 띄운 앱이라 사람의 문서가 그 안에서 숨은 채 남는다 #>
    param($App, [ValidateSet('Word', 'Excel', 'PPT')][string]$Kind, [bool]$WasRunning = $false)
    if ($null -eq $App) { return $false }
    $open = -1
    try {
        $open = switch ($Kind) {
            'Word'  { [int]$App.Documents.Count }
            'Excel' { [int]$App.Workbooks.Count }
            'PPT'   { [int]$App.Presentations.Count }
        }
        # 보호된 보기로 열린 문서는 위 모음에 안 든다 — 사람이 받은 파일 · 메일 첨부를 열면 그 꼴로 열린다
        try { $open += [int]$App.ProtectedViewWindows.Count } catch { }
    } catch { }
    # 못 셌으면(-1) 안 끈다 — 남은 숨은 앱은 정리할 수 있지만 닫힌 사람의 문서는 못 되돌린다
    $quit = ($open -eq 0) -and -not ($Kind -eq 'PPT' -and $WasRunning)
    if ($quit) {
        try { $App.Quit() } catch { }
    } elseif ($open -gt 0 -and $Kind -ne 'PPT') {
        # 숨은 앱에 남은 문서는 사람이 보지도 닫지도 저장하지도 못한다. 파워포인트는 숨기기를 거부해 창이 이미 보인다
        try { if (-not $App.Visible) { $App.Visible = $true } } catch { }
    }
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($App) } catch { }
    return $quit
}
