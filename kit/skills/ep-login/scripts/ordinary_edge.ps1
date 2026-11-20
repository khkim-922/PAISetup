# 사람의 평소 Edge(디버깅 포트 없음)를 윈도 UI 자동화로 보는 눈과 누르는 손 — 입구(ep_login.js)만 부른다. 무엇을 누를지는 입구가 가린다
# (받는 손의 epConfirm). 여기는 본 것을 알리고 시킨 단추 하나를 누르는 일만 든다 — 탭 · 창 · 쿠키에는 손대지 않는다.
#
# 부르는 꼴:
#     powershell -NoProfile -ExecutionPolicy Bypass -File ordinary_edge.ps1
#   환경변수 EP_ORDINARY_PROFILE — 볼 Edge 의 프로필 폴더. 안 주면 사람의 평소 Edge(--user-data-dir 없이 뜬 브라우저 프로세스 — 입구가 주소를
#     넘기면 탭이 열리는 그 Edge)다. 프로필을 주는 것은 가짜 SSO 로 재는 검사(설정 저장소 _check/skills/ep-login/check_session.js)가 버리는 프로필을 볼 때뿐이다.
#
# 주고받는 꼴 — 표준 입력의 한 줄마다 한 번 본다:
#   look      → 표준 출력에 JSON 한 줄: {"dialogs":[{"i":번호,"title":창 제목,"message":글,"buttons":단추 수,
#               "edit":입력 칸이 있나}]}
#   press <i> → 바로 앞 look 의 물음 i 의 첫 단추를 누르고 {"pressed":i,"button":단추 이름} 한 줄(못 누르면 {"pressed":-1,"why":…})
#   tabs      → 창마다 앞 탭의 주소(주소창)와 모든 탭의 제목(탭 줄)을 읽어, EP 에 맞는 수만 JSON 한 줄로 낸다:
#               {"browsers":브라우저 프로세스 수,"windows":창 수,"unread":탭 줄도 주소창도 안 읽힌 Edge 창 수,"portal":앞 탭이 포털 호스트인 창 수,
#                "login":앞 탭이 로그인 화면 호스트인 창 수,"titled":제목이 포털 제목인 탭 수}
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

# 탭 줄과 주소창을 세어 낸다 — 둘 다 안 잡히는 창은 unread 로 센다(그 창은 못 본 것이지 포털이 없는 것이 아니다)
function Tabs($ids) {
    $count = @{ browsers = @($ids).Count; windows = 0; unread = 0; portal = 0; login = 0; titled = 0 }
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
            if ($omnibox) {
                $address = ''
                try { $address = $omnibox.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { }
                $h = HostOf $address
                if ($h -and $PortalHosts -contains $h) { $count.portal++ }
                elseif ($h -and $LoginHosts -contains $h) { $count.login++ }
            }
        } catch { $count.unread++ }                   # 보는 사이 닫힌 창 — 못 본 것으로 센다
    }
    $count
}

$IdsEvery = 8            # 브라우저 프로세스를 다시 묻는 눈금(보기 수) — 평소 Edge 가 안 떠 있던 판은 못 찾은 동안 매번 묻는다
$seen = @()
$ids = @()
$looks = 0
while ($true) {
    $line = [Console]::In.ReadLine()
    if (-not $line) { break }
    if ($line -like 'press *') {
        $i = [int]$line.Substring(6)
        $answer = @{ pressed = -1; why = '그 물음이 없다' }
        if ($i -ge 0 -and $i -lt $seen.Count) {
            try {
                $button = $seen[$i].FindFirst($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Button))
                $name = $button.Current.Name                  # 누르면 창이 닫혀 이름을 못 읽는다 — 먼저 읽는다
                $button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
                $answer = @{ pressed = $i; button = $name }
            } catch { $answer = @{ pressed = -1; why = $_.Exception.Message } }
        }
        [Console]::Out.WriteLine(($answer | ConvertTo-Json -Compress)); [Console]::Out.Flush()
        continue
    }
    if (-not $ids.Count -or $looks % $IdsEvery -eq 0) { $ids = @(Browsers) }   # 프로세스 묻기는 비싸다 — 몇 번에 한 번, 못 찾았으면 매번
    $looks++
    if ($line -eq 'tabs') {
        [Console]::Out.WriteLine(((Tabs $ids) | ConvertTo-Json -Compress)); [Console]::Out.Flush()
        continue
    }
    $dialogs = @(); $seen = @()
    foreach ($top in (Windows $ids)) {
        try {
            foreach ($pair in (Dialogs $top)) {
                $win, $js = $pair
                $texts = @($js.FindAll($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Text)) | ForEach-Object { $_.Current.Name })
                $buttons = @($win.FindAll($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Button))).Count
                $edit = [bool]$js.FindFirst($Scope::Descendants, (Cond $AE::ControlTypeProperty $Kind::Edit))
                $dialogs += @{ i = $seen.Count; title = $win.Current.Name; message = ($texts -join ' '); buttons = $buttons; edit = $edit }
                $seen += $win
            }
        } catch { }                                   # 보는 사이 닫힌 창 — 다음 look 이 다시 본다
    }
    [Console]::Out.WriteLine((@{ dialogs = $dialogs } | ConvertTo-Json -Compress -Depth 4)); [Console]::Out.Flush()
}
