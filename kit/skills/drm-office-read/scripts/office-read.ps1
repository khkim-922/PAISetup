<#
    drm-office-read 의 읽는 부품 — Fasoo 에이전트가 도는 PC 의 오피스를 태워 문서에서 글자와 「글 밖」의 셈을 뽑는 함수만 든다.
    본체(인자 · 대상 모으기 · 화면 · 파일 쓰기 · 끝 정리)는 안 든다 — 스킬의 `read-drm.ps1` 이 그 본체고, 제 꼴로 내는 앱은 제 본체를
    쓰고 여기를 점 소싱한다. 실어도 아무것도 돌지 않고 표준 출력에 아무것도 안 낸다.
    점 소싱으로 싣는다 — 세션 규칙이 먼저다(Open-OwnedDocument · Assert-* 를 여기가 부른다):
        . (Join-Path $PSScriptRoot 'office-session.ps1')
        . (Join-Path $PSScriptRoot 'office-read.ps1')

    왜 앱을 태우나: Fasoo DRM 은 파일을 통째로 자기 컨테이너로 감싼다. 머리 바이트가 `%PDF-`·`PK` 가 아니게 되므로 어떤 파서
    (PDFium·pdfplumber·python-docx·openpyxl)도 형식 인식 단계에서 죽는다. 정식 오피스 앱은 그 보호를 복호해 주므로 그것을 태운다.

    계약 — $DRM_OFFICE_READ_CONTRACT 가 든다. 부르는 쪽은 실은 뒤 이 값을 제가 아는 판과 견준다.
      · 앱 이름은 'Word' | 'Excel' | 'PPT' — $HANDLER 가 확장자를 이 이름으로 보내고, office-session.ps1 의 Kind 와 같다
      · New-OfficeJob · Set-OfficeJobKill · Join-OfficeJob — 띄운 오피스를 이 프로세스의 Job(KILL_ON_JOB_CLOSE)에 묶는 손
      · Get-FileHead · Test-PlainFormat — 머리 바이트 · 감겼나
      · New-OfficeApp -AppName -SpawnedPids ([ref]해시) -Job — 앱 하나를 띄워 돌려준다. 띄우기 전에 없던 PID 만 해시(PID → 앱 이름)에
        더하고 Job 에 넣는다. 파워포인트를 띄울 때 $PptWasRunning 을 부르는 쪽의 스크립트 범위에 둔다(아래)
      · Read-WithWord · Read-WithExcel · Read-WithPPT -App -LiteralPath → @{ Text = [string]; Visual = [hashtable] }
        Visual 의 열쇠는 영어다 — tables · images · shapes · formulas · charts · fields. 0 인 열쇠는 없다. 파워포인트는 글 없는
        낱 도형(그림 · 도형을 안 가른다)을 images 에 센다. 사람 말로 옮기는 것은 부르는 쪽 몫이다(read-drm.ps1 의 Format-Visual)
      · Format-Cell · Get-PptLeafShapes · Measure-*Visual · Add-Count — 위 셋이 쓰는 부품. 따로 불러도 된다
      · 상수 — $HANDLER · $PROCESS_OF · $INV · $XL_ERROR_TEXT · $PPT_GROUP_DEPTH_MAX · $PPT_SEAT_LEGEND · $PPT_SEAT_TAG · $PPT_BREAKS ·
        $PPT_CELL_BREAK · $PPT_CELL_SAME_PT
      · 파워포인트 글은 머리 한 줄($PPT_SEAT_LEGEND) 뒤 장마다 도형을 위→아래 · 왼→오른으로 세워 줄마다 [위 · 왼] 꼬리표를 앞세운다.
        표의 합친 칸은 첫 칸에만 글을 두고 덮인 칸은 비운다
    판을 올리는 자 — 함수 이름 · 인자 · 내는 꼴(열쇠 포함) · Job 의 뜻이 바뀌면 1 을 올린다. 함수를 더하거나 안을 고치는 것은 안 올린다.

    $PptWasRunning — New-OfficeApp 이 파워포인트를 띄우기 전에 그 앱이 떠 있었나를 $script: 범위에 둔다. 점 소싱한 함수의 $script: 는
    실은 쪽의 스크립트 범위라 그 변수는 부르는 쪽 것이다 — 끝에서 Exit-OfficeApp -WasRunning 에 넘긴다. 돌려주지 않는 까닭: 돌려주면
    New-OfficeApp 의 내는 꼴이 앱 하나에서 둘로 바뀌어 부르는 쪽 셋이 다 풀어 받아야 한다.

    진단은 Write-Warning 으로 낸다 — 표준 출력에는 아무것도 안 낸다. 표준 출력이 제 계약인 앱(JSON 한 줄 따위)은 경고 흐름을 제 자리로
    보낸다 — 경고를 내는 함수는 고급 함수라 `-WarningVariable` · `-WarningAction` 이 선다(New-OfficeApp 은 안에서 부른 것까지 모은다).
#>

$DRM_OFFICE_READ_CONTRACT = 1

# 어느 확장자를 어느 앱이 드나. PDF 는 워드가 든다 — Acrobat COM 은 이 기계에서
# 클래스 미등록(0x80040154)이라 못 탄다.
$HANDLER = @{
    '.doc'  = 'Word';  '.docx' = 'Word';  '.rtf'  = 'Word';  '.pdf' = 'Word'
    '.xls'  = 'Excel'; '.xlsx' = 'Excel'; '.xlsm' = 'Excel'; '.csv' = 'Excel'
    '.ppt'  = 'PPT';   '.pptx' = 'PPT'
}
$PROCESS_OF = @{ 'Word' = 'WINWORD'; 'Excel' = 'EXCEL'; 'PPT' = 'POWERPNT' }
$INV = [Globalization.CultureInfo]::InvariantCulture
# 엑셀의 Value2 는 오류 칸(#N/A 등)을 음수 정수로 준다 — 그대로 적으면 -2146826246 이 진짜 값처럼 보인다
$XL_ERROR_TEXT = @{ -2146826288 = '#NULL!'; -2146826281 = '#DIV/0!'; -2146826273 = '#VALUE!'; -2146826265 = '#REF!'
                    -2146826259 = '#NAME?'; -2146826252 = '#NUM!'; -2146826246 = '#N/A' }
# 묶음 안 묶음을 어디까지 펴나 — 그 아래는 도형 하나로 센다
$PPT_GROUP_DEPTH_MAX = 20
# 파워포인트 글의 도형 꼬리표 — 읽는 모델이 나란한 칸의 머리말과 값을 같은 「왼」끼리 짝짓는 근거다.
# 만든 차례(z)대로 내면 머리말 바로 뒤에 다른 칸의 값이 서고 모델은 그것을 그 머리말의 값으로 읽는다
$PPT_SEAT_LEGEND = '(도형 앞 [위 · 왼] 은 그 도형이 장 안에 놓인 자리다 — 포인트, 왼쪽 위가 0)'
$PPT_SEAT_TAG = '[위 {0:0} · 왼 {1:0}]'
# 파워포인트 글의 문단 끝(CR)과 문단 안 줄 나눔(VT) — 꼬리표 줄 안에 남으면 읽는 도구마다 줄이 붙거나 끊긴다
$PPT_BREAKS = @([string][char]13, [string][char]11)
$PPT_CELL_BREAK = '<br>'
# 표 칸 두 개가 같은 합친 칸인지 가르는 자리 상자의 허용 차(pt) — 다른 칸은 칸 크기만큼 어긋난다
$PPT_CELL_SAME_PT = 0.5

# ── 띄운 앱은 이 프로세스에 묶는다 ───────────────────────────────────────
# 오피스는 COM 서버라 이 PowerShell 의 자식이 아니다 — 부르는 쪽이 시한으로 이 프로세스를 끊으면 본체의
# finally 가 안 돌고, 숨은 앱이 문서를 연 채 남는다. 그래서 띄운 PID 를 Job(KILL_ON_JOB_CLOSE)에 넣는다 —
# 이 프로세스가 어떻게 끝나든 Job 손잡이가 닫히며 그 앱이 함께 끝난다. 사람이 먼저 띄운 앱은 안 든다
# (띄우기 전후의 PID 차이만 넣는다). ⚠ 그 몇 초 사이 사람이 이 숨은 인스턴스로 문서를 열면 함께 닫힌다 —
# 이 판이 띄운 앱을 끝에서 강제로 끝내는 규칙(파워포인트의 DRM 훅)과 같은 몫이다.
# 한 프로세스에 두 번 실려도 선다 — 같은 이름의 형을 두 번 더하면 Add-Type 이 진다
if (-not ('DrmRead.Job' -as [type])) {
    Add-Type -Namespace DrmRead -Name Job -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr CreateJobObject(IntPtr attrs, string name);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr info, uint size);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
[DllImport("kernel32.dll", SetLastError = true)] public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool CloseHandle(IntPtr handle);
'@
}

function New-OfficeJob {
    <# 끝내기 규칙을 켠 Job 손잡이를 낸다 — 못 만들면 Zero 를 내고 알린다(그때는 PID 로만 쫓는다) #>
    [CmdletBinding()]
    param()
    $job = [DrmRead.Job]::CreateJobObject([IntPtr]::Zero, $null)
    if ($job -eq [IntPtr]::Zero) { Write-Warning 'Job 을 못 만들었다 — 끊기면 띄운 오피스가 남을 수 있다'; return $job }
    if (-not (Set-OfficeJobKill -Job $job -On $true)) { Write-Warning 'Job 에 끝내기 규칙을 못 걸었다 — 끊기면 띄운 오피스가 남을 수 있다' }
    return $job
}

function Set-OfficeJobKill {
    <# Job 의 끝내기 규칙을 켜거나($On) 끈다 — 끈 뒤 손잡이를 닫으면 묶인 앱은 산다 #>
    param([IntPtr]$Job, [bool]$On)
    if ($Job -eq [IntPtr]::Zero) { return $false }
    # JOBOBJECT_EXTENDED_LIMIT_INFORMATION — LimitFlags 는 x64 · x86 모두 16 바이트 자리, 구조 크기는 포인터 크기가 가른다
    $size = if ([IntPtr]::Size -eq 8) { 144 } else { 112 }
    $info = [Runtime.InteropServices.Marshal]::AllocHGlobal($size)
    try {
        for ($i = 0; $i -lt $size; $i++) { [Runtime.InteropServices.Marshal]::WriteByte($info, $i, 0) }
        $flags = if ($On) { 0x2000 } else { 0 }                                  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        [Runtime.InteropServices.Marshal]::WriteInt32($info, 16, $flags)
        return [DrmRead.Job]::SetInformationJobObject($Job, 9, $info, [uint32]$size)   # JobObjectExtendedLimitInformation
    } finally { [Runtime.InteropServices.Marshal]::FreeHGlobal($info) }
}

function Join-OfficeJob {
    <# 띄운 PID 들을 Job 에 넣는다 — 못 넣은 것은 알린다 #>
    [CmdletBinding()]
    param([IntPtr]$Job, [int[]]$Pids)
    if ($Job -eq [IntPtr]::Zero) { return }
    foreach ($id in $Pids) {
        $h = [DrmRead.Job]::OpenProcess(0x0101, $false, $id)        # PROCESS_TERMINATE | PROCESS_SET_QUOTA
        if ($h -eq [IntPtr]::Zero -or -not [DrmRead.Job]::AssignProcessToJobObject($Job, $h)) {
            Write-Warning "띄운 오피스(PID $id)를 Job 에 못 넣었다 — 끊기면 남을 수 있다"
        }
        if ($h -ne [IntPtr]::Zero) { [void][DrmRead.Job]::CloseHandle($h) }
    }
}

function Read-HeadBytes {
    <# 파일 머리 $Count 바이트. 오피스가 열어 쥔 파일도 읽게 쓰기 · 지우기를 함께 허락해 연다 —
       `ReadAllBytes` 는 그 파일에서 공유 위반으로 진다. #>
    param([string]$LiteralPath, [int]$Count)
    $fs = [System.IO.File]::Open($LiteralPath, 'Open', 'Read', 'ReadWrite, Delete')
    try {
        $buf = New-Object byte[] $Count
        $n = 0
        while ($n -lt $Count) { $r = $fs.Read($buf, $n, $Count - $n); if ($r -le 0) { break }; $n += $r }
        if ($n -lt $Count) { $buf = if ($n -eq 0) { [byte[]]@() } else { $buf[0..($n - 1)] } }
        return ,[byte[]]$buf
    } finally { $fs.Dispose() }
}

function Get-FileHead {
    <# 파일 머리 8바이트를 눈으로 읽을 꼴로. DRM 이 감쌌으면 `. DRMONE` 처럼 나온다. #>
    param([string]$LiteralPath)
    $bytes = Read-HeadBytes $LiteralPath 8
    $n = $bytes.Length
    if ($n -eq 0) { return '(빈 파일)' }
    -join ($bytes[0..($n - 1)] | ForEach-Object {
        if ($_ -ge 32 -and $_ -lt 127) { [char]$_ } else { '.' }
    })
}

function Test-PlainFormat {
    <# 감기지 않은 원래 형식인가. 감겼으면 $false — 그때만 이 부품이 값을 낸다. #>
    param([string]$LiteralPath)
    $bytes = Read-HeadBytes $LiteralPath 4
    if ($bytes.Length -lt 4) { return $false }
    $sig = -join ($bytes[0..3] | ForEach-Object { [char]$_ })
    return ($sig -eq '%PDF' -or $sig.StartsWith('PK') -or $sig.StartsWith('{\rt') -or
            ($bytes[0] -eq 0xD0 -and $bytes[1] -eq 0xCF))   # 옛 오피스 OLE
}

function New-OfficeApp {
    <# 앱 하나를 띄운다. 파일마다 띄우면 건당 수 초씩 붙으므로 앱은 재사용한다.
       띄우기 전에 없던 PID 만 이 판의 것으로 쳐 $SpawnedPids 에 더하고 Job 에 넣는다 — 사람이 쓰던 프로세스는 안 든다 #>
    [CmdletBinding()]
    param([string]$AppName, [ref]$SpawnedPids, [IntPtr]$Job)
    $beforePids = @(Get-Process -Name $PROCESS_OF[$AppName] -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    switch ($AppName) {
        'Word' {
            $a = New-Object -ComObject Word.Application
            $a.Visible = $false
            $a.DisplayAlerts = 0          # wdAlertsNone — 변환 대화창이 뜨면 무인 실행이 멈춘다
        }
        'Excel' {
            $a = New-Object -ComObject Excel.Application
            $a.Visible = $false
            $a.DisplayAlerts = $false
        }
        'PPT' {
            # ⚠ 파워포인트는 Visible=$false 를 거부하고 하나만 뜬다(그 앱만 그렇다) — 떠 있었으면 그 앱에 붙는다.
            #   부르는 쪽의 스크립트 범위에 둔다(머리말) — 끝에서 그 앱을 안 끄는 근거다
            $script:PptWasRunning = ($beforePids.Count -gt 0)
            $a = New-Object -ComObject PowerPoint.Application
        }
    }
    $newPids = @(Get-Process -Name $PROCESS_OF[$AppName] -ErrorAction SilentlyContinue |
                 Where-Object { $beforePids -notcontains $_.Id } | Select-Object -ExpandProperty Id)
    foreach ($id in $newPids) { $SpawnedPids.Value[$id] = $AppName }
    if ($newPids.Count -gt 0) { Join-OfficeJob -Job $Job -Pids $newPids }
    return $a
}

# ── 글 밖에 있는 것을 센다 ────────────────────────────────────────────────
# 글자만 뽑으면 표 · 그림 · 수식 · 차트는 뽑히지 않거나 평탄해진다. 그래서 「글로 담기지 않는
# 것이 이 문서에 몇 개 있나」를 문서 자신에게 묻는다 — 셀 수 있는 값이라 0 이면 그림이 필요
# 없다고 단정할 수 있다. 글자 수로는 못 가른다: 몇 자부터 짧은가는 문서마다 달라 답이 없고,
# 셀 값만으로 완결된 시트와 수식 하나가 전부인 문서가 같은 길이로 나온다.
# 묻는 이름은 앱마다 다르다. 못 묻는 항목은 0 으로 둔다 — 판의 차이로 없는 속성이 있다.
# 열쇠는 영어(머리말의 계약) — 사람 말로 옮기는 것은 부르는 쪽이 한다.
function Add-Count {
    param([hashtable]$Into, [string]$Key, [scriptblock]$Get)
    try {
        $v = [int](& $Get)
        if ($v -gt 0) { $Into[$Key] = [int]$Into[$Key] + $v }
    } catch { }
}

function Measure-WordVisual {
    param($Doc)
    $c = @{}
    Add-Count $c 'tables'   { $Doc.Tables.Count }
    Add-Count $c 'images'   { $Doc.InlineShapes.Count }
    Add-Count $c 'shapes'   { $Doc.Shapes.Count }
    Add-Count $c 'formulas' { $Doc.OMaths.Count }
    Add-Count $c 'fields'   { $Doc.Fields.Count }
    return $c
}

function Measure-ExcelVisual {
    param($Book)
    $c = @{}
    foreach ($sheet in $Book.Sheets) {
        $charts = 0; $pictures = 0; $shapes = 0
        try { $charts = [int]$sheet.ChartObjects().Count } catch { }
        try { $pictures = [int]$sheet.Pictures().Count } catch { }
        try { $shapes = [int]$sheet.Shapes.Count } catch { }
        # Shapes 는 차트 · 그림까지 든다 — 빼지 않으면 한 차트가 「차트」와 「도형」으로 두 번 선다
        Add-Count $c 'shapes' { $shapes - $charts - $pictures }
        Add-Count $c 'charts' { $charts }
        Add-Count $c 'images' { $pictures }
    }
    Add-Count $c 'charts' { $Book.Charts.Count }   # 시트째 차트 — 위 고리가 안 센다
    return $c
}

function Get-PptLeafShapes {
    <# 도형 모음을 묶음 안까지 편 낱 도형의 열 — 묶음(msoGroup 6)과 묶음이 든 개체 틀(msoPlaceholder 14)은 제 글이
       없고 GroupItems 가 글을 든다. 안 펴면 묶음 안 글은 안 나오고 묶음 안 그림은 「글 밖」에 안 세어져, 「글 밖이
       0 이면 글자가 전부다」가 거짓이 된다. 깊이 상한을 넘는 묶음은 그 자리에서 도형 하나로 센다.
       빌린 규격 — 동료 저장소 sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1` 의
       `Write-PPTShape`(2ef0ddb3f65c): 묶음이 든 개체 틀 · 깊이 상한. 손으로 따라간다 #>
    param($Shapes, [int]$Depth = 0)
    foreach ($shape in $Shapes) {
        $isGroup = $false
        try {
            $isGroup = ($shape.Type -eq 6)
            if (-not $isGroup -and $shape.Type -eq 14) { $isGroup = ([int]$shape.PlaceholderFormat.ContainedType -eq 6) }
        } catch { }
        if ($isGroup -and $Depth -lt $PPT_GROUP_DEPTH_MAX) {
            $items = $null
            try { $items = $shape.GroupItems } catch { }
            if ($items) { Get-PptLeafShapes -Shapes $items -Depth ($Depth + 1); continue }
        }
        $shape
    }
}

function Measure-PptVisual {
    param($Pres)
    # 장마다 글 없는 낱 도형을 센다 — 글이 든 도형과 표는 글자 추출이 이미 담았다. 그림과 도형을 안 가르고 images 하나에 센다
    $c = @{}
    foreach ($slide in $Pres.Slides) {
        foreach ($shape in (Get-PptLeafShapes -Shapes $slide.Shapes)) {
            try {
                if ($shape.HasTable -ne 0) { continue }
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) { continue }
            } catch { }
            $c['images'] = [int]$c['images'] + 1
        }
    }
    return $c
}

function Read-WithWord {
    param($App, [string]$LiteralPath)
    # 인자 셋 — 경로 · ConfirmConversions=$false · ReadOnly=$true.
    # ReadOnly 를 켜야 원본에 쓰기 잠금이 안 걸리고 DRM 이 수정으로 보지 않는다.
    # 사람이 같은 파일을 열어 두었으면 그 문서를 돌려받는다 — 읽기만 하고 닫지 않는다(office-session.ps1)
    $isPdf = ([System.IO.Path]::GetExtension($LiteralPath).ToLower() -eq '.pdf')
    if ($isPdf) { Assert-WordPdfQuiet $App }
    $session = Open-OwnedDocument -Kind 'Word' -Collection $App.Documents -Open { $App.Documents.Open($LiteralPath, $false, $true) }
    $doc = $session.Document
    try {
        $text = [string]$doc.Content.Text
        if ($isPdf) { Assert-PdfConverted $text }
        return @{ Text = $text; Visual = (Measure-WordVisual $doc) }
    } finally {
        Close-OwnedDocument $session    # SaveChanges=$false — 원본을 절대 안 고친다
    }
}

function Get-Decimals([string]$Fmt) {
    if ($Fmt -match '\.(0+)') { return $Matches[1].Length }
    return 0
}

function Format-Cell {
    <# Value2 한 칸 → 사람이 읽는 글. 수는 날짜 · 시각 · 백분율 · 천 단위 · 고정 소수만 열의 서식으로 되살리고
       나머지는 값 그대로다 — 보이는 글자(.Text)는 칸이 좁으면 날짜 대신 `########` 이 오고 칸마다 묻는 것이라,
       값을 한 번에 받고 뜻이 갈리는 꼴만 되살린다. 통화 기호 · 사용자 꼴 · 칸마다 다른 꼴은 날값으로 온다 —
       열마다 서식 하나만 묻기 때문이다.
       빌린 규격 — mail-secretary `secretary/office_read.ps1` 의 `Format-Cell`(9f9cf9b) · 오류 칸 표는 동료 저장소
       sejuone-cloud/pgpt-one-click-connect `office-com-read/scripts/read-office.ps1`(2ef0ddb3f65c). 손으로 따라간다 #>
    param($Value, [string]$Fmt)
    if ($null -eq $Value) { return '' }
    if ($Value -is [int]) { $e = $XL_ERROR_TEXT[$Value]; if ($e) { return $e } }
    if ($Value -isnot [double]) { return [string]$Value }
    $f = ($Fmt -replace '"[^"]*"', '' -replace '\[[^\]]*\]', '').ToLower()   # 따옴표 글 · [$-412] 꼴은 서식의 뜻이 아니다
    try {
        if ($f -match '[yd]') {
            $d = [DateTime]::FromOADate($Value)
            if ($f -match 'h') { return $d.ToString('yyyy-MM-dd HH:mm', $INV) }
            return $d.ToString('yyyy-MM-dd', $INV)
        }
        if ($f -match 'h' -and $f -match ':') { return [DateTime]::FromOADate($Value).ToString('HH:mm', $INV) }
    } catch { return $Value.ToString('R', $INV) }
    if ($f -match '%') { return ($Value * 100).ToString('F' + (Get-Decimals $f), $INV) + '%' }
    if ($f -match '#,##0') { return $Value.ToString('N' + (Get-Decimals $f), $INV) }
    if ($f -match '^0\.0+$') { return $Value.ToString('F' + (Get-Decimals $f), $INV) }
    return $Value.ToString('R', $INV)
}

function Read-WithExcel {
    param($App, [string]$LiteralPath)
    # UpdateLinks=0 · ReadOnly=$true
    $session = Open-OwnedDocument -Kind 'Excel' -Collection $App.Workbooks -Open { $App.Workbooks.Open($LiteralPath, 0, $true) }
    $book = $session.Document
    try {
        $out = [System.Text.StringBuilder]::new()
        foreach ($sheet in $book.Sheets) {
            [void]$out.AppendLine("### 시트: $($sheet.Name)")
            $used = $sheet.UsedRange
            $rows = [int]$used.Rows.Count; $cols = [int]$used.Columns.Count
            # 시트의 값을 한 번에 받는다 — 칸마다 COM 을 넘으면 칸 수만큼 프로세스를 오가 큰 시트 한 장이 몇 분이다
            $vals = $used.Value2
            if ($null -eq $vals) { continue }
            if ($vals -isnot [Array]) { $one = New-Object 'object[,]' 1, 1; $one[0, 0] = $vals; $vals = $one; $rows = 1; $cols = 1 }
            $lo1 = $vals.GetLowerBound(0); $lo2 = $vals.GetLowerBound(1)
            $sample = [Math]::Min(2, $rows)          # 첫 자료 줄의 서식 — 머리 줄은 대개 글이라 서식이 「일반」이다
            $fmts = @()
            for ($k = 1; $k -le $cols; $k++) {
                $f = ''
                try { $f = [string]$used.Cells.Item($sample, $k).NumberFormat } catch { }
                $fmts += $f
            }
            for ($r = 0; $r -lt $rows; $r++) {
                $cells = New-Object string[] $cols
                for ($k = 0; $k -lt $cols; $k++) { $cells[$k] = Format-Cell -Value $vals[($r + $lo1), ($k + $lo2)] -Fmt $fmts[$k] }
                # 행으로 묶는다 — 셀마다 줄을 끊으면 표라는 것이 사라져 모델이 못 알아본다.
                [void]$out.AppendLine('| ' + ($cells -join ' | ') + ' |')
            }
        }
        return @{ Text = $out.ToString(); Visual = (Measure-ExcelVisual $book) }
    } finally {
        Close-OwnedDocument $session
    }
}

function Get-PptCellBox {
    <# 표 칸 도형의 자리 상자 @(왼, 위, 너비, 높이)(pt). 못 읽으면 $null — 그 칸은 합친 칸으로 안 가른다 #>
    param($CellShape)
    try { return , @([double]$CellShape.Left, [double]$CellShape.Top, [double]$CellShape.Width, [double]$CellShape.Height) }
    catch { return $null }
}

function Test-PptSameBox {
    <# 두 상자가 $PPT_CELL_SAME_PT 안으로 같나 — 파워포인트 개체 모형에는 합침 여부 속성이 없어, 같은 상자가 곧 같은 합친 칸이다 #>
    param($A, $B)
    if ($null -eq $A -or $null -eq $B) { return $false }
    for ($i = 0; $i -lt 4; $i++) { if ([Math]::Abs($A[$i] - $B[$i]) -gt $PPT_CELL_SAME_PT) { return $false } }
    return $true
}

function Read-WithPPT {
    param($App, [string]$LiteralPath)
    # 사람이 같은 파일을 열어 두었으면 그 발표를 돌려받는다 — 읽기만 하고 닫지 않는다(office-session.ps1)
    # 경로 · ReadOnly=$true · Untitled=$false · WithWindow=$false
    $session = Open-OwnedDocument -Kind 'PPT' -Collection $App.Presentations -Open { $App.Presentations.Open($LiteralPath, $true, $false, $false) }
    $pres = $session.Document
    try {
        $out = [System.Text.StringBuilder]::new()
        [void]$out.AppendLine($PPT_SEAT_LEGEND)
        foreach ($slide in $pres.Slides) {
            [void]$out.AppendLine("### 장 $($slide.SlideIndex)")
            # 묶음 안 도형도 슬라이드 자리를 주므로 편 뒤 한 번에 세운다 — 위→아래 · 왼→오른, 같은 자리면 만든 차례
            $z = 0
            $seated = foreach ($leaf in (Get-PptLeafShapes -Shapes $slide.Shapes)) {
                $z++
                $top = 0.0; $left = 0.0
                try { $top = [double]$leaf.Top; $left = [double]$leaf.Left } catch { }
                [pscustomobject]@{ Shape = $leaf; Top = $top; Left = $left; Z = $z }
            }
            foreach ($seat in @($seated | Sort-Object Top, Left, Z)) {
                $shape = $seat.Shape
                $tag = $PPT_SEAT_TAG -f $seat.Top, $seat.Left
                if ($shape.HasTextFrame -and $shape.TextFrame.HasText) {
                    $text = [string]$shape.TextFrame.TextRange.Text
                    foreach ($b in $PPT_BREAKS) { $text = $text.Replace($b, [Environment]::NewLine) }
                    [void]$out.AppendLine("$tag $text")
                }
                if ($shape.HasTable -ne 0) {
                    [void]$out.AppendLine("$tag 표")
                    try {
                        $tbl = $shape.Table
                        $boxes = @{}
                        for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                            $rowCells = @()
                            for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                                $cellShape = $tbl.Cell($r, $c).Shape
                                $box = Get-PptCellBox $cellShape
                                $boxes["$r,$c"] = $box
                                # 합친 칸의 덮인 자리는 첫 칸과 같은 글 · 같은 상자를 돌려준다 — 비워 두어야 값이 칸 수만큼 안 더해진다
                                if ((Test-PptSameBox $box $boxes["$r,$($c - 1)"]) -or (Test-PptSameBox $box $boxes["$($r - 1),$c"])) {
                                    $rowCells += ''
                                    continue
                                }
                                $cell = [string]$cellShape.TextFrame.TextRange.Text
                                foreach ($b in $PPT_BREAKS) { $cell = $cell.Replace($b, $PPT_CELL_BREAK) }
                                $rowCells += $cell
                            }
                            [void]$out.AppendLine('| ' + ($rowCells -join ' | ') + ' |')
                        }
                    } catch { }
                }
            }
        }
        return @{ Text = $out.ToString(); Visual = (Measure-PptVisual $pres) }
    } finally {
        Close-OwnedDocument $session
    }
}
