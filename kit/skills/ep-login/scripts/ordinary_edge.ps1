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
$DialogDepth = 3          # 물음 창(RootView)이 브라우저 창 아래 놓이는 깊이의 위 끝 — 페이지 나무까지 내려가지 않는다
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

$IdsEvery = 8             # 브라우저 프로세스를 다시 묻는 눈금(보기 수) — 평소 Edge 가 안 떠 있던 판은 못 찾은 동안 매번 묻는다
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
