"""판정 한 벌 — 검사마다 사본을 뜨던 `report`·`show`·`edge` 와 종료코드 계약을 모은다.

좌표 — AI-prompt-helper 이슈 #52 ① · AI-prompt-helper 결정 0029(종료코드) · 아뜰리에 `_check/_verdict.py`.

세 방언은 축이 달라 셋 다 산다:

  report(이름, ok, 상세=())  상세는 **실패에만** 찍힌다 (계약 판정)
  show(라벨, 실측, 기대)     실측값을 **늘** 찍는다 (값 대조)
  edge(문구)                 **통과할 때도 보여야 하는 경계.** 실패 상세에 실으면 정작
                             경고가 필요한 통과 화면에서 안 보인다 — 한 도구 호출 프로브의
                             「부름이 하나뿐이면 미측정」이 그렇게 묻힌 것이 이 손의 실측이다
  unmeasured(이름, 까닭)     **판정이 아니다** — 아예 안 잰 자리. 초록에도 빨강에도 안 든다

계수는 이 모듈이 든다 — 부르는 쪽은 `fails()`·`passes()`·`unmeasureds()` 로 읽는다. 요약
문구는 파일마다 뜻이 달라 여기서 안 정한다. 다만 **초록 줄에는 「무엇을 쟀나」(건수·범위)를
함께 찍는다** — 「전부 통과」는 *여기까지* 통과인데 범위를 안 적으면 전부로 읽힌다.

⚠ **그 건수를 손으로 적지 않는다** — `len(passes())` 가 이번 판에서 **실제로 선** 판정을
  센다. 손으로 적은 수는 판정이 늘어도 절이 통째로 사라져도 그대로라, 마지막 줄만 옛말을
  하고 종료코드는 글자 하나 안 바뀐다.

⚠ **사본을 새로 뜨지 않는다** — `python -X utf8 _check/<검사>.py` 로 돌면 이 폴더가 경로에
  이미 있어 `from _verdict import …` 한 줄이면 된다.

⚠ **무는 순간 `sys.stdout` 이 utf-8 로 선다** — 판정 글자가 cp949 에 없어서다. 까닭은 아래
  곁주석이 든다.
"""
import sys

# 한글 Windows 는 stdout 을 cp949·strict 로 잡는다 — 판정 문구의 한글이 그 표에 없는 자리를
# 만나면 **검사를 다 끝내고 찍다가** 죽는다. 통과한 검사가 실패로 읽히는 자리다.
# 진짜 콘솔은 무사하고 **리디렉션·파이프에서만** 나므로 `> log` 나 `| head` 를 거는 순간에만
# 보인다 — 리눅스 CI 도 못 잡는다.
# **여기 서는 까닭** — 판정을 찍는 검사가 다 이 모듈을 문다. 진입점마다 손으로 붙이면 새
# 검사가 날 때마다 빠지고, 빠진 자리는 아무 뜻도 없는 빨강으로만 보인다.
# stderr 는 파이썬이 `backslashreplace` 로 잡아 애초에 안 죽으므로 안 든다.
sys.stdout.reconfigure(encoding="utf-8")

# 종료코드 계약 — 진본은 `_check/README.md` §종료코드 이고 그 뜻을 이 셋이 든다(결정 0029).
# 훅도 CI 도 화면 문구를 안 읽고 코드만 보므로 이 갈림이 곧 계약이다.
EXIT_OK = 0             # 쟀고 맞다
EXIT_MISMATCH = 1       # 어긋났다
EXIT_UNMEASURED = 2     # 못 쟀다 — 초록이 아니다. 아예 안 잰 자리다

FAILS = []
PASSES = []
UNMEASURED = []


class Unmeasured(SystemExit):
    """「못 쟀다」로 그 자리에서 나가는 손 — 말하고 **2** 로 나간다.

    ⚠ **`raise SystemExit("글자")` 를 쓰지 않는다.** 파이썬은 그 글자를 stderr 로 찍고
      **무조건 1** 로 나가, 화면은 「[안 잼]」이라고 맞는 말을 하는데 훅·CI 만 조용히
      「어긋났다」로 읽는다 — 못 쟀다가 판정으로 새는 자리다.

    ⚠ **글자는 짓는 자리에서 찍는다.** 종료코드를 숫자로 줘야 2 로 나가는데, 그러면
      파이썬이 아무것도 안 찍어 사람이 까닭을 잃는다. `str(예외)` 는 그 글자를 그대로
      들려 보낸다 — 검사가 「이 부름이 서나」를 물을 때 그 말로 문다.
    """

    def __init__(self, why):
        super().__init__(EXIT_UNMEASURED)
        self.why = str(why)
        print(self.why)

    def __str__(self):
        return self.why


def report(name, ok, detail=()):
    """계약 판정 — 상세는 실패에만. 통과에도 보여야 하는 말은 `edge()` 로."""
    (PASSES if ok else FAILS).append(name)
    print(f"[{'OK ' if ok else 'NG '}] {name}")
    for row in detail if not ok else ():
        print(f"       {row}")


def show(label, got, want):
    """값 대조 — 실측값을 늘 찍는다. 초록이어도 무엇을 봤는지가 남는다."""
    ok = got == want
    (PASSES if ok else FAILS).append(label)
    print(f"  {'✅' if ok else '❌'} {label}: {got!r}" + ("" if ok else f"  ← 기대 {want!r}"))


def edge(text):
    """통과할 때도 보여야 하는 경계 문구 — 판정이 아니라 범위의 고지다."""
    print(f"  ⚠ {text}")


def unmeasured(name, why):
    """재려던 자리가 비었다 — **판정을 안 낸 것이지 통과가 아니다**(종료코드 2)."""
    UNMEASURED.append(name)
    print(f"[?  ] {name} — 못 쟀다: {why}")


def fails():
    """어긋난 판정의 이름들 — 요약·종료코드는 부르는 쪽이 이걸로 세운다."""
    return list(FAILS)


def passes():
    """맞은 판정의 이름들 — **초록 줄의 건수가 여기서 나온다.**

    `edge()` 는 안 든다. 저것은 판정이 아니라 범위의 고지라, 세면 「몇 건을 쟀나」가
    부풀어 도로 거짓말이 된다.
    """
    return list(PASSES)


def unmeasureds():
    """못 잰 자리의 이름들 — 하나라도 있으면 초록이 아니다(`EXIT_UNMEASURED`)."""
    return list(UNMEASURED)
