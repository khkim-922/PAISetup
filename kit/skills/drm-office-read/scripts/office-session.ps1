<#
    drm-office-read 스크립트들이 함께 쓰는 오피스 세션 규칙 — 사람이 열어 둔 오피스와 문서는 건드리지 않는다.
    점 소싱으로 싣는다:  . (Join-Path $PSScriptRoot 'office-session.ps1')

    파워포인트는 사용자 하나에 하나만 뜨는 COM 서버라 New-Object 가 사람이 쓰는 파워포인트에 붙는다. 그대로
    Quit 하면 사람의 창과 저장 안 한 발표가 경고 없이 닫힌다. 같은 파일을 이미 열어 두었으면 Open 이 사람의
    문서 개체를 그대로 돌려준다 — 그것을 닫거나 Saved 를 찍으면 사람의 변경이 사라진다. 워드 · 엑셀은 보통 새
    인스턴스로 뜨지만 같은 규칙을 건다 — 붙은 자리였을 때 잃는 것이 사람의 문서라서다.
#>

function Test-OfficeRunning([string]$ProcessName) {
    return @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue).Count -gt 0
}

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

function Exit-OfficeApp {
    <# 남은 문서가 없고 사람이 쓰던 파워포인트에 붙은 것이 아닐 때만 끈다. 끄지 않았으면 거짓을 돌려준다 #>
    param($App, [ValidateSet('Word', 'Excel', 'PPT')][string]$Kind, [bool]$WasRunning = $false)
    if ($null -eq $App) { return $false }
    $open = -1
    try {
        $open = switch ($Kind) {
            'Word'  { [int]$App.Documents.Count }
            'Excel' { [int]$App.Workbooks.Count }
            'PPT'   { [int]$App.Presentations.Count }
        }
    } catch { }
    # 못 셌으면(-1) 안 끈다 — 남은 숨은 앱은 정리할 수 있지만 닫힌 사람의 문서는 못 되돌린다
    $quit = ($open -eq 0) -and -not ($Kind -eq 'PPT' -and $WasRunning)
    if ($quit) { try { $App.Quit() } catch { } }
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($App) } catch { }
    return $quit
}
