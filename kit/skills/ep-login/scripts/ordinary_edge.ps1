# 사람의 평소 Edge(디버깅 포트 없음)를 윈도 UI 자동화로 보는 눈과 누르는 손 — 입구(ep_login.js)만 부른다. 무엇을 누를지는 입구가 가린다
# (회사 자리 값 ep_places.js 의 epConfirm). 여기는 본 것을 알리고 시킨 단추 하나를 누르는 일만 든다 — 탭 · 창 · 쿠키에는 손대지 않는다.
#
# 부르는 꼴:
#     powershell -NoProfile -ExecutionPolicy Bypass -File ordinary_edge.ps1
#   환경변수 EP_ORDINARY_PROFILE — 볼 Edge 의 프로필 폴더. 안 주면 사람의 평소 Edge(--user-data-dir 없이 뜬 브라우저 프로세스 — 입구가 주소를
#     넘기면 탭이 열리는 그 Edge)다. 프로필을 주는 것은 가짜 SSO 로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)가 버리는 프로필을 볼 때뿐이다.
#
# 주고받는 꼴 — 뜨면 먼저 준비 줄 {"ready":true} 하나를 낸다(UI 자동화를 다 실었다 — 부르는 쪽은 이 줄까지를 뜨는 시간으로, 그 뒤만 보기의
#   시간으로 잰다). 그 뒤 표준 입력의 한 줄마다 한 번 본다:
#   look    → 표준 출력에 JSON 한 줄: {"dialogs":[{"i":번호,"title":창 제목,"message":글,"buttons":단추 수,
#               "edit":입력 칸이 있나}]}
#   press <i> → 바로 앞 look 의 물음 i 의 첫 단추를 누르고 {"pressed":i,"button":단추 이름} 한 줄(못 누르면 {"pressed":-1,"why":…})
#   tabs      → 창마다 앞 탭의 주소(주소창)와 모든 탭의 제목(탭 줄)을 읽어, EP 에 맞는 수만 JSON 한 줄로 낸다:
#               {"browsers":브라우저 프로세스 수,"windows":창 수,"unread":탭 줄도 주소창도 안 읽힌 Edge 창 수,"portal":앞 탭이 포털 호스트인 창 수,
#                "login":앞 탭이 로그인 화면 호스트인 창 수,"titled":제목이 포털 제목인 탭 수,
#                "committed":앞 탭이 포털 호스트이고 그 탭에 화면이 섰다는 증거가 있는 창 수}
#               증거는 둘 중 하나다 — 이 눈이 사는 동안 그 탭(UI 자동화의 RuntimeId 로 가린다)의 주소창에 로그인 화면 호스트를 봤다 · 그 탭의 이름이
#               첫 화면이 안 온 탭의 자리 이름($Placeholders 와 이 눈이 배운 것)이 아니다. 이름이 비었거나 앞 탭을 못 찾으면 증거가 아니다.
#               배우기 — 주소창이 포털에 머문 채 그 탭의 이름이 바뀌면 바뀌기 전 이름은 자리 이름이었다(바뀐 뒤 이름이 자리 이름이면 안 배운다).
#               배운 것은 이 프로세스 안에만 산다
#               ⚠ 사람의 다른 탭의 주소 · 제목은 이 프로세스 밖으로 안 낸다 — 견주기만 하고 세어 낸다. 견줄 값은 환경변수로 받는다:
#               EP_TAB_PORTAL · EP_TAB_LOGIN 호스트 이름(쉼표로 여럿 · 포트는 안 본다) · EP_TAB_TITLE 포털 탭의 제목(통째로 같아야 센다 · 비면 제목은 안 본다 · 대소문자를 가린다)
#   빈 줄 · 끝 → 끝낸다(입구가 죽어 표준 입력이 닫혀도 여기서 끝난다 — 남지 않는다)
# 첫 단추가 「확인」인 까닭 — 윈도의 Chromium 물음 창은 「확인」을 앞에 둔다(views 의 PlatformStyle::kIsOkButtonLeading). 물음 창의 꼴
# (JavaScriptTabModalDialogViewViews · 제목 「<호스트>의 메시지」)은 references/SOURCES.md 「잰 것」이 든다.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$AE = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Kind = [System.Windows.Automation.ControlType]
$Walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$RawWalker = [System.Windows.Automation.TreeWalker]::RawViewWalker
$DialogDepth = 3          # 물음 창(RootView)이 브라우저 창 아래 놓이는 깊이의 위 끝 — 페이지 나무까지 내려가지 않는다
# Edge 가 탭의 접근성 이름 끝에 붙이는 메모리 사용량 꼬리(` - 메모리 사용량 - 21.3 MB` · 영문 ` - Memory usage - 21.3 MB`) — 붙는 때와
#   안 붙는 때가 갈려, 떼지 않고 견주면 같은 포털 탭을 판마다 다르게 센다
$MemoryTail = [regex]' - [^-]+ - [0-9][0-9.,]* ?[KMG]B$'
# Edge 가 첫 화면이 아직 안 온 탭에 다는 자리 이름 — 그 사이 주소창은 연 주소(포털)를 그대로 보여, 이 이름이 「포털 화면이 섰다」와 「막 열었다」를
#   가르는 하나뿐인 표다. 한국어판 · 영문판(--lang=en-US)의 것이다(references/SOURCES.md 「잰 것」). 다른 말의 Edge 는 이 눈이 바뀌는 것을 보고 배운다
$Placeholders = @('제목 없음', 'Untitled')
$Profile = $env:EP_ORDINARY_PROFILE

function Cond($property, $value) { New-Object System.Windows.Automation.PropertyCondition($property, $value) }

# 볼 Edge 의 브라우저 프로세스 — 창은 다 이 프로세스가 든다
function Browsers {
    Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" | Where-Object {
        $line = [string]$_.CommandLine
        if ($line -match '--type=') { return $false }
        # 그 폴더 그대로만 — 이름이 그 폴더로 시작하는 다른 폴더(…\a 와 …\a2)는 아니다
        if ($Profile) { return $line -match ('--user-data-dir="?' + [regex]::Escape($Profile) + '"?(\s|$)') }
        return $line -notmatch '--user-data-dir'
    } | ForEach-Object { [int]$_.ProcessId }
}

function Windows($ids) {
    $found = @()
    foreach ($id in $ids) {
        $found += @($AE::RootElement.FindAll($Scope::Children, (Cond $AE::ProcessIdProperty $id)))
    }
    $found
}

# 브라우저 창 아래 얕은 자리의 물음 창 — 그 안에 자바스크립트 물음의 꼴(JavaScriptTabModalDialogViewViews)이 든 창만
function Dialogs($top) {
    $out = @()
    $queue = New-Object System.Collections.Queue
    $queue.Enqueue(@($top, 0))
    while ($queue.Count) {
        $el, $depth = $queue.Dequeue()
        if ($depth -gt 0 -and $el.Current.ControlType -eq $Kind::Window) {
            $js = $el.FindFirst($Scope::Descendants, (Cond $AE::ClassNameProperty 'JavaScriptTabModalDialogViewViews'))
            if ($js) { $out += ,@($el, $js) }
            continue
        }
        if ($depth -ge $DialogDepth) { continue }
        $child = $Walker.GetFirstChild($el)
        while ($child) { $queue.Enqueue(@($child, ($depth + 1))); $child = $Walker.GetNextSibling($child) }
    }
    , $out                                            # 짝 하나만 있어도 짝의 목록으로 낸다 — 안 싸면 PowerShell 이 그 짝을 풀어 낸다
}

$PortalHosts = @(([string]$env:EP_TAB_PORTAL).ToLower().Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$LoginHosts = @(([string]$env:EP_TAB_LOGIN).ToLower().Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$PortalTitle = [string]$env:EP_TAB_TITLE

# 주소창의 글에서 호스트 이름만 — 주소창은 스킴을 떼고 보이기도 한다(「swp.posco.net/…」). 포트 · 경로는 뗀다
function HostOf([string]$text) {
    $rest = ($text.Trim() -replace '^[a-zA-Z][a-zA-Z0-9+.-]*://', '')
    $hostPort = ($rest -split '[/?#]', 2)[0]
    if ($hostPort -match '^\[([^\]]+)\]') { return $Matches[1].ToLower() }
    return ($hostPort -split ':', 2)[0].ToLower()
}

# 창의 앞 탭(탭 줄에서 골라진 탭) — { id: RuntimeId · name: 메모리 꼬리를 뗀 이름 }. 못 찾으면 $null
function Front($tabs) {
    foreach ($t in $tabs) {
        try {
            if ($t.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected) {
                return @{ id = ($t.GetRuntimeId() -join '.'); name = $MemoryTail.Replace($t.Current.Name.Trim(), '').Trim() }
            }
        } catch { }
    }
    $null
}

$LoginSeen = New-Object 'System.Collections.Generic.HashSet[string]'   # 주소창에 로그인 화면 호스트를 보인 탭의 열쇠
$Learned = New-Object 'System.Collections.Generic.HashSet[string]'     # 이 눈이 배운 자리 이름
$PortalName = @{}                                                        # 탭의 열쇠 → 주소창이 포털에 머무는 동안 본 이름
function Placeholder([string]$name) { ($Placeholders -ccontains $name) -or $Learned.Contains($name) }

# 앞 탭의 증거를 갈무리하고, 앞 탭이 포털이면 그 탭에 화면이 섰다는 증거가 있나를 낸다 — kind 는 주소창의 호스트가 portal · login · 그 밖('')
function Committed($tabs, [string]$kind) {
    $front = Front $tabs
    if (-not $front) { return $false }
    $id = $front.id; $name = $front.name
    if ($kind -ne 'portal') {
        $PortalName.Remove($id)
        if ($kind -eq 'login') { [void]$LoginSeen.Add($id) }
        return $false
    }
    if ($name) {
        $was = $PortalName[$id]
        if ($was -and $was -cne $name -and -not (Placeholder $name) -and $was -cne $PortalTitle) { [void]$Learned.Add($was) }
        $PortalName[$id] = $name
    }
    if ($LoginSeen.Contains($id)) { return $true }
    return ([bool]$name -and -not (Placeholder $name))
}

# 탭 줄과 주소창을 세어 낸다 — 둘 다 안 잡히는 창은 unread 로 센다(그 창은 못 본 것이지 포털이 없는 것이 아니다)
function Tabs($ids) {
    $count = @{ browsers = @($ids).Count; windows = 0; unread = 0; portal = 0; login = 0; titled = 0; committed = 0 }
    foreach ($top in (Windows $ids)) {
        try {
            $count.windows++
            # 브라우저 칸(창 바로 아래의 BrowserRootView)에서 찾는다 — 창에서 한 번에 찾으면 탭이 그린 화면(Chrome_RenderWidgetHostHWND)이 창
            # 아래 여럿 선 뒤로는 브라우저 칸 아래를 안 훑어 탭 줄 · 주소창을 놓친다(references/SOURCES.md 「잰 것」). 페이지 안은 안 훑는다
            $roots = @(); $child = $RawWalker.GetFirstChild($top)
            while ($child) { if ($child.Current.ClassName -eq 'BrowserRootView') { $roots += $child }; $child = $RawWalker.GetNextSibling($child) }
            if (-not $roots.Count) { $roots = @($top) }
            $tabs = @(); $omnibox = $null
            foreach ($root in $roots) {
                $tabs += @($root.FindAll($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::TabItem)))
                if (-not $omnibox) { $omnibox = $root.FindFirst($Scope::Descendants, (Cond $AE::ClassNameProperty 'OmniboxViewViews')) }
            }
            if (-not $tabs.Count -and -not $omnibox) { $count.unread++; continue }
            # 제목은 통째로 같아야 센다 — 일부만 견주면 포털 제목을 든 다른 화면(로그인 화면 따위)의 탭도 포털로 센다
            if ($PortalTitle) { foreach ($t in $tabs) { if ($MemoryTail.Replace($t.Current.Name.Trim(), '') -ceq $PortalTitle) { $count.titled++ } } }
            $kind = ''
            if ($omnibox) {
                $address = ''
                try { $address = $omnibox.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { }
                $h = HostOf $address
                if ($h -and $PortalHosts -contains $h) { $count.portal++; $kind = 'portal' }
                elseif ($h -and $LoginHosts -contains $h) { $count.login++; $kind = 'login' }
            }
            if (Committed $tabs $kind) { $count.committed++ }
        } catch { $count.unread++ }                   # 보는 사이 닫힌 창 — 못 본 것으로 센다
    }
    $count
}

# 바로 앞 Look 이 본 물음 $i 의 첫 단추를 누르고 그 답을 낸다 — 누르면 창이 닫혀 이름을 못 읽어 이름을 먼저 읽는다
function Press([int]$i) {
    if ($i -lt 0 -or $i -ge $script:seen.Count) { return @{ pressed = -1; why = '그 물음이 없다' } }
    try {
        $button = $script:seen[$i].FindFirst($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Button))
        $name = $button.Current.Name
        $button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        return @{ pressed = $i; button = $name }
    } catch { return @{ pressed = -1; why = $_.Exception.Message } }
}

# 볼 Edge 의 창마다 물음 창을 보고 그 꼴을 낸다 — 본 창은 $script:seen 에 번호 차례로 남긴다(Press 가 그 번호로 누른다)
function Look($ids) {
    $dialogs = @(); $script:seen = @()
    foreach ($top in (Windows $ids)) {
        try {
            foreach ($pair in (Dialogs $top)) {
                $win, $js = $pair
                $texts = @($js.FindAll($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Text)) | ForEach-Object { $_.Current.Name })
                $buttons = @($win.FindAll($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Button))).Count
                $edit = [bool]$js.FindFirst($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Edit))
                $dialogs += @{ i = $script:seen.Count; title = $win.Current.Name; message = ($texts -join ' '); buttons = $buttons; edit = $edit }
                $script:seen += $win
            }
        } catch { }                                   # 보는 사이 닫힌 창 — 다음 look 이 다시 본다
    }
    @{ dialogs = $dialogs }
}

# 답 하나를 표준 출력에 JSON 한 줄로 낸다 — 입구가 줄마다 기다린다
function Answer($value, [int]$depth = 2) { [Console]::Out.WriteLine(($value | ConvertTo-Json -Compress -Depth $depth)); [Console]::Out.Flush() }

$IdsEvery = 8            # 브라우저 프로세스를 다시 묻는 눈금(보기 수) — 평소 Edge 가 안 떠 있던 판은 못 찾은 동안 매번 묻는다
$seen = @()
$ids = @()
$looks = 0
Answer @{ ready = $true }
# 줄 받기 고리 — 한 줄을 읽어 그 물음의 손가락을 부르고 답을 낸다
while ($true) {
    $line = [Console]::In.ReadLine()
    if (-not $line) { break }
    if ($line -like 'press *') { Answer (Press ([int]$line.Substring(6))); continue }
    if (-not $ids.Count -or $looks % $IdsEvery -eq 0) { $ids = @(Browsers) }   # 프로세스 묻기는 비싸다 — 몇 번에 한 번, 못 찾았으면 매번
    $looks++
    if ($line -eq 'tabs') { Answer (Tabs $ids); continue }
    Answer (Look $ids) 4
}
