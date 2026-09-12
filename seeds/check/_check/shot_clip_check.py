"""긴 지면을 띠로 잘라 찍을 때 clip 이 **전체 쪽 좌표**인가 — playwright 의 축.

좌표 — 이 자가 난 자리는 아뜰리에 `_check/shot_clip_check.py`(36408d5 · 이슈 번호는 없다) ·
브라우저를 판이 아니라 실행 파일로 집는 차례는 아뜰리에 결정 0175(곁 `_browser.mjs` 가 그 쌍둥이) ·
씨앗 규율은 claude-config 결정 0040.

    python -X utf8 _check/shot_clip_check.py

**왜 이 검사가 있나.** 지면이 한 화면보다 길면 띠로 잘라 찍는다 —
`page.screenshot(full_page=True, clip={"y": i * H, …})` 로 **i 번째 띠**를 집는 꼴이다. 그 `y` 가
**전체 쪽 좌표**라야 그 뜻이 서는데, 뷰포트 기준이면 매 타일이 같은 자리를 찍어 **둘째 타일부터
전부 첫 화면**이 된다. 그림은 나오므로 오류가 안 나고, 사람이 눈으로 보기 전까지 아무도 모른다.

⚠ **playwright 의 문서가 이 조합을 못박지 않는다.** `full_page` 와 `clip` 을 같이 주는 자리라 판이
  오르면 갈릴 수 있고, 갈리면 조용하다 — 그래서 잰다.

재는 것 둘 —

  ① **양성 대조** — 검체 쪽이 뷰포트보다 실제로 길다. 이것이 안 서면 아래 판정은 「한 화면을
     네 번 본」 것이라 늘 초록이 난다 — 재는 자가 곧 재이는 것이 되는 자리다.
  ② **띠마다 제 띠를 집는다** — 띠마다 다른 빨강값을 깔고 **픽셀로** 확인한다. 글자로 재면 폰트가
     없는 자리에서 흔들리고, 그 흔들림을 이 검사의 답으로 오해하게 된다.

**받은 저장소가 무엇을 줘야 도나** — playwright(파이썬)와 Pillow 가 든 파이썬 하나, 그리고 크로미움
계열 하나. 앱을 안 문다 — 이 자는 저장소의 코드를 한 줄도 안 읽는다. 브라우저는 환경변수로 짚는다:
`PW_EXE`(손으로 못박은 실행 파일) · `PLAYWRIGHT_BROWSERS_PATH`(받아 둔 자리 · 판 번호를 안 읽는다).
둘 다 없으면 PATH 의 크로미움 계열 → playwright 기본값 → msedge → chrome 으로 내려가고, 끝내 못
띄우면 초록이 아니라 **「못 쟀다」(2)** 로 나간다. 무엇으로 쟀는지는 경계 줄이 찍는다.

⚠ **지면을 찍는 파이썬이 앱에도 있으면 쌍둥이가 생긴다** — 브라우저 집는 차례가 이 파일과 앱에
  따로 산다. 차례를 바꿀 때는 둘 다 바꾼다(아뜰리에 0175). 검사에서만 브라우저를 띄우는 저장소는
  쌍둥이가 없다.

**안 재는 것** — 그 저장소가 **실제로 띠를 자르는 코드**(여기는 playwright 의 축만 잰다 — 그 축
위에 선 코드는 그 저장소가 제 검사로 잰다) · **playwright 판을 박는 일**(이 판에서 그렇더라는
실측이지 규칙이 아니다) · 띠 경계의 한 픽셀(가운데 점 하나만 읽는다 — 축이 갈리면 띠째 갈리므로
가운데로 족하다) · 어느 브라우저가 **옳은** 브라우저인가(크로미움 계열 하나면 축은 같다).

망도 토큰도 안 쓴다. 브라우저는 띄운다 — 헤드리스 한 판이다.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

from _verdict import EXIT_MISMATCH, EXIT_OK, Unmeasured, edge, fails, passes, show

W, H = 300, 400
# 띠마다 다른 빨강값 — 어느 띠가 찍혔나를 **픽셀로** 안다.
REDS = (10, 90, 170, 250)
# 띠 수의 진본은 위 목록 하나다 — 손으로 두 자리에 적으면 값을 늘릴 때 한쪽만 따라온다.
BANDS = len(REDS)
HTML = ("<style>body{margin:0}div{height:%dpx}</style>" % H) + "".join(
    f'<div style="background:rgb({c},0,0)"></div>' for c in REDS)

# ── 브라우저를 **판에 안 매이게** 집는다 — 곁 `_browser.mjs` 와 같은 규칙 (아뜰리에 0175)
#
# playwright 는 **제가 받은 판만 안다.** 레지스트리에 박힌 번호와 실물이 어긋나면 브라우저가
# **있는데도 없다고** 말한다. 그런데 우리가 재는 것은 브라우저의 판이 아니라 playwright 의 축이라,
# 크로미움이 무엇이든 하나만 서 있으면 잴 수 있다 — 그래서 판을 맞추는 대신 실행 파일을 직접
# 가리킨다. 이름 목록은 `.exe` 를 손으로 여덟 줄 적지 않고 파생한다.
EXE_NAMES = ("chrome", "chromium", "headless_shell", "chrome-headless-shell")
EXE_MATCH = frozenset(EXE_NAMES) | {f"{n}.exe" for n in EXE_NAMES}
# **헤드리스 셸을 먼저 집는다 — 늘 헤드리스로 띄우기 때문이다.** 취향이 아니라 실측이 세운
# 순서다: 이 자리에서 `chrome.exe` 는 못 뜨고(`spawn UNKNOWN`) 헤드리스 셸은 뜬다.
HEADLESS_FIRST = ("chrome-headless-shell", "headless_shell")
HEADLESS_MATCH = frozenset(HEADLESS_FIRST) | {f"{n}.exe" for n in HEADLESS_FIRST}
# ⚠ **`chrome` 은 이 목록에 안 넣는다** — 이름을 맞추면 `chrome.exe` 가 걸리는데 그 파일이 못 뜨는
#   기계가 있다. 여기는 배포판이 깔아 두는 이름만 든다.
ON_PATH = ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable")
# 윈도우는 확장자가 이름의 일부다 — `PATHEXT` 를 안 얹으면 `chromium.exe` 를 못 본다.
PATH_EXTS = tuple((os.environ.get("PATHEXT") or ".COM;.EXE;.BAT;.CMD").split(";")) if os.name == "nt" else ("",)
# 실행 파일을 못 찾았을 때 내려가는 사다리 — 빈 글자가 playwright 기본값이다.
CHANNELS = ("", "msedge", "chrome")


def _runnable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)   # isfile 은 링크를 따라간다 — 끊긴 링크가 여기서 걸린다


def _under_browsers_path():
    """`PLAYWRIGHT_BROWSERS_PATH` 아래 아무 크로미움 — **판 번호를 안 읽는다.**"""
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not root:
        return None
    queue = [root]                        # 얕은 곳부터(너비 우선) — `…/chromium` 지름길 링크가 먼저 걸린다
    fallback = None                       # 헤드리스 셸이 끝내 안 나오면 이것을 쓴다
    while queue:
        try:
            with os.scandir(queue.pop(0)) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            continue                      # 못 읽는 자리는 건너뛴다
        subdirs = []
        for e in entries:
            if e.name in EXE_MATCH and _runnable(e.path):
                if e.name in HEADLESS_MATCH:
                    return e.path         # 우리가 쓸 꼴이다 — 더 볼 것 없다
                if fallback is None:
                    fallback = e.path     # 머리 달린 판 — 셸이 없을 때만 쓴다
            if e.is_dir():
                subdirs.append(e.path)
        queue.extend(subdirs)
    return fallback


def _on_path():
    """`PATH` 의 크로미움 계열 — 하위 프로세스를 안 띄우고 파일만 조회한다."""
    for name in ON_PATH:
        for folder in (os.environ.get("PATH") or "").split(os.pathsep):
            if not folder:
                continue
            for ext in PATH_EXTS:
                cand = os.path.join(folder, name + ext)
                if _runnable(cand):
                    return cand
    return None


def browser_exe():
    """쓸 실행 파일 — 못 찾으면 None(= playwright 기본값에 맡긴다).

    차례: `PW_EXE`(손으로 못박은 자리) → 받아 둔 크로미움 → `PATH` 의 크로미움 계열.
    """
    return os.environ.get("PW_EXE") or _under_browsers_path() or _on_path() or None


def launch(p):
    """(브라우저, 무엇으로 집었나) — 못 띄우면 **시도한 것을 다 달아** 올린다.

    ⚠ 마지막 오류만 남기면 사다리 앞쪽이 왜 실패했는지가 가려져, 브라우저가 있는데도 엉뚱한
      안내(`playwright install`)를 하게 된다.
    """
    tried = []
    exe = browser_exe()
    if exe:
        try:
            return p.chromium.launch(headless=True, executable_path=exe), exe
        except Exception as exc:
            tried.append(f"{exe} — {exc}")
    for channel in CHANNELS:
        try:
            kw = {"channel": channel} if channel else {}
            said = channel or "playwright 기본값 — 실행 파일을 못 찾아 제 레지스트리에 맡겼다"
            return p.chromium.launch(headless=True, **kw), said
        except Exception as exc:
            tried.append(f"{channel or 'playwright 기본값'} — {exc}")
    raise RuntimeError("크로미움 계열이 없다 — Edge/Chrome 을 깔거나 `playwright install chromium`, "
                       "아니면 `PW_EXE` 로 실행 파일을 짚는다. 시도한 것: " + " · ".join(tried))


def measure(page, image_open):
    """검체를 열어 축을 잰다 — 양성 대조부터 세우고 띠마다 판정을 찍는다."""
    tall = int(page.evaluate("document.documentElement.scrollHeight"))
    show("전체 쪽이 뷰포트보다 길다 (양성 대조)", tall, H * BANDS)
    for i, red in enumerate(REDS):
        png = page.screenshot(full_page=True,
                              clip={"x": 0, "y": i * H, "width": W, "height": H})
        im = image_open(io.BytesIO(png)).convert("RGB")
        show(f"clip.y={i * H} 가 {i + 1}번째 띠를 집는다", im.getpixel((W // 2, H // 2))[0], red)


def main():
    try:
        from playwright.sync_api import sync_playwright
        from PIL import Image
    except ImportError as exc:
        raise Unmeasured(f"[안 잼] 뽑는 자가 없다 — {exc}. playwright 와 Pillow 가 든 파이썬으로 "
                         "부른다(`pip install playwright Pillow` · `playwright install chromium`)") from exc

    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "clip_probe.html"          # 검체는 저장소 밖에 짓는다 — 나무를 안 더럽힌다
        probe.write_text(HTML, encoding="utf-8")
        with sync_playwright() as p:
            try:
                browser, said = launch(p)
            except Exception as exc:
                raise Unmeasured(f"[안 잼] 브라우저를 못 띄웠다 — {exc}") from exc
            edge(f"**무엇으로 쟀나** — {said}")
            try:
                page = browser.new_page(viewport={"width": W, "height": H})
                page.goto(probe.resolve().as_uri(), wait_until="load")
                measure(page, Image.open)
            finally:
                browser.close()

    edge("**playwright 판을 안 박는다** — 이 판에서 그렇더라는 실측이지 규칙이 아니다. 판을 올릴 때 다시 돌린다")
    edge("**띠를 실제로 자르는 코드는 안 본다** — 여기는 playwright 의 축만 잰다. 그 축 위에 선 코드는 그 저장소가 잰다")

    print()
    if fails():
        print(f"{len(fails())}건 어긋남 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"전부 통과 (판정 {len(passes())}건 — 양성 대조 하나 · 띠마다 하나. 축은 clip 과 "
          "full_page 를 같이 준 자리 하나다)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
