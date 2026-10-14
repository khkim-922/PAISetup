# 로컬 HTML 페이지를 기본 브라우저로 연다 — 설치기 끝의 「제공기능」 · 설치 창의 「제공기능」 링크 · 알림 창이 같이 쓴다.
#
# ⚠ **`.html` 파일 연결로 열지 않는다.** 기본 브라우저는 `https` 연결에 서고 `.html` 연결은 그와 따로 논다 — 그 연결을 아직
#   안 고른 PC(맨바닥 VDI)에서 파일을 그대로 띄우면 윈도우가 앱 고르기 창부터 띄운다. 그래서 `https` 에 선 앱의 여는 명령
#   (`HKCR\<ProgId>\shell\open\command`)에 그 파일의 주소(`file:///…`)를 넣어 띄우고, 그 앱을 못 찾으면 파일 연결에 맡긴다.
# 던지면 부르는 쪽이 「못 열었다」로 읽는다.

function Open-InBrowser([string]$Page) {
  $uri = ([Uri]$Page).AbsoluteUri
  $id  = (Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice' -ErrorAction SilentlyContinue).ProgId
  $cmd = if ($id) { (Get-ItemProperty -LiteralPath "Registry::HKEY_CLASSES_ROOT\$id\shell\open\command" -ErrorAction SilentlyContinue).'(default)' }
  if ("$cmd" -match '^\s*"([^"]+)"\s*(.*)$' -and (Test-Path -LiteralPath $Matches[1])) {
    $exe = $Matches[1]; $rest = $Matches[2]
    $arg = if ($rest.Contains('%1')) { $rest.Replace('%1', $uri) } else { "$rest $uri".Trim() }
    Start-Process -FilePath $exe -ArgumentList $arg | Out-Null
    return
  }
  Start-Process -FilePath $Page | Out-Null
}
