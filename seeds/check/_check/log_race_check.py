"""여럿이 한꺼번에 찍어도 줄이 안 섞이나 — 콘솔 tee 의 꼬리를 잰다.

좌표 — 아뜰리에 #339 · AI-prompt-helper #37 · 씨앗 규율은 claude-config 결정 0040.

`print` 한 번은 본문과 개행을 **`write` 두 번**으로 쓴다. 요청마다 스레드를 세우는 서버라면
(`ThreadingHTTPServer`) 그 둘 사이에 남의 `write` 가 드는데, tee 의 꼬리 버퍼가 스레드
공유면 두 문의 본문이 한 줄로 붙고 빈 줄이 하나 더 난다 — **사고 뒤에 읽을 기록이 그
자리에서 어긋난다.** 잠금으로는 못 막는다: 잠금은 `write` 한 번씩만 감싸 본문과 개행 둘을
못 묶는다.

**이것은 게이트웨이도 앱도 아닌 파이썬 로깅 일반의 성질이라 씨앗에 산다.** 저장소마다 다른
것은 **배관 이름뿐**이고 그것을 인자로 받는다 — 아래 「어떻게 주나」.

**장면이 둘이고 둘은 서로 다른 사고다.**

  · **엮인 판**(결정론) — 스레드 둘이 본문만 쓰고 서로를 기다렸다 개행을 쓴다.
    빗장(`threading.Barrier`)이 그 엇갈림을 **손으로 만든다** — 운에 안 맡긴다.
    **이빨은 여기서 문다.**
  · **한꺼번에 판**(실측) — 진짜 `print` 로 여럿이 동시에 찍는다. 끝 조건(섞인 줄 0)이 이
    자리다. 엇갈림은 인터프리터 몫이라 **안 나는 판은 못 잰 것이지 맞은 것이 아니다** —
    그래서 되돌린 사본을 무는 자리는 위가 든다.

**실물 배선을 잰다** — tee 를 손으로 짓지 않고 저장소가 준 여는 손을 부른다. 핸들러·형식·
감싸기가 다 그 안에서 서므로, 배선이 갈리면 여기가 같이 빨개진다. 콘솔 쪽은 `io.StringIO`
가 받는다 — 판정 화면이 수천 줄에 안 덮이게.

**어떻게 주나.** 배관을 안 주면 「못 쟀다」(2)로 나간다.

    python -X utf8 _check/log_race_check.py --self
    python -X utf8 _check/log_race_check.py --root <저장소> --watch logs \
        --plumb app.log:_TeeStream:own
    python -X utf8 _check/log_race_check.py --root <저장소> --watch logs \
        --plumb app.server:_TeeStream:_own_log --log-into app.config:LOG_FILE

  · `--plumb 모듈:tee:여는손` — 갈아 끼울 tee 클래스와 그것을 세우는 손. 여는 손이 돌려줄
    것은 `(자리, 못 열었으면 사유)` 다
  · `--log-into 모듈:이름` — 여는 손이 자리를 **인자로 안 받고 설정에서 읽을 때** 쓴다. 그
    이름에 자리를 앉히고 여는 손을 빈손으로 부른다. 안 주면 `여는손(자리)` 로 부른다
  · `--root` — 그 모듈이 임포트되게 앞에 놓을 나무 뿌리 (기본: 지금 자리)
  · `--watch` — 저장소가 기록을 남기는 자리. 끝에 **늘어난 것**을 본다. 절대값으로 재면
    실물을 띄우는 형제 검사가 남긴 것에 여기가 빨개진다. 안 주면 그 자리는 안 잰다
  · `--self` — 배관 없이 씨앗이 제 본보기 tee 로 돈다

인자는 환경변수로도 받는다 — `LOG_RACE_PLUMB` · `LOG_RACE_LOG_INTO` · `LOG_RACE_ROOT` ·
`LOG_RACE_WATCH`. 훅·CI 에 태울 때 명령줄을 안 고치려는 자리다.

**받는 저장소의 tee 가 들어야 하는 것** — 되돌린 사본이 그 위에 서므로 이것이 계약이다:
`console`·`logger`·`level`·`echo` 를 받는 `__init__` · 차례를 세우는 `lock` · 줄 단위로
`logger.log` 하는 `write`. 그리고 여는 손이 세운 `sys.stdout` 에 그 `logger` 가 달려 있어야
한다 — 이름을 손으로 안 적고 거기서 받는다. 하나라도 없으면 「못 쟀다」(2)다.

⚠ **시각 머리의 폭을 안 잰다.** 형식이 저장소마다 달라 앞을 잘라 내면 씨앗이 남의 형식을
  박게 된다. 대신 **꼬리로 가른다** — 성한 줄은 기대 한 줄로 끝나고 그 앞에 본문이 또 있지
  않다. 붙은 줄은 꼬리가 성해도 앞에 본문이 하나 더 들어 걸리고, 더 난 빈 줄은 어느 꼬리와도
  안 맞는다.

⚠ **`--self` 는 재는 자가 곧 재이는 것이다** — 씨앗이 제 본보기 tee 를 잰다. 그 초록은 *이
  검사가 물 줄 안다*는 말이지 어느 저장소의 배선이 성하다는 말이 아니다. 이빨(③)이 그
  자리를 떠받친다.

**안 재는 것**은 마감의 `edge()` 목록이 든다 — 그 줄들이 진본이라 여기 또 안 적는다.

토큰도 망도 브라우저도 안 쓴다. 임시 폴더에서 돌고 저장소에 한 자도 안 남긴다.
"""
import argparse
import importlib
import io
import logging
import os
import shutil
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from _verdict import (EXIT_MISMATCH, EXIT_OK, EXIT_UNMEASURED, Unmeasured,
                      edge, fails, passes, report, show)

THREADS = 8                     # 한꺼번에 찍는 스레드 — 끝 조건 「여럿이 동시에 print」
LINES = 200                     # 스레드마다 찍는 줄 수
BODY = "본문" * 12              # 한 줄의 몸통 — 섞이면 두 이름이 한 줄에 든다
NAMES = ["가", "나", "다", "라", "마", "바", "사", "아"][:THREADS]

# 감싼 stdout 이 들고 있어야 하는 것 — 되돌린 사본이 이 위에 선다(머리말 「계약」).
NEEDS = ("console", "logger", "level", "echo", "lock")

STOP = []                       # 못 잰 사유 — 하나라도 차면 종료코드 2


# ── 장면 ──────────────────────────────────────────────────────────────────────

def say(who, i):
    """찍을 한 줄 — 기대 집합도 이 손이 짓는다(둘을 따로 적으면 갈린다)."""
    return f"[{who}] {i:03d} {BODY}"


def run(one, names):
    threads = [threading.Thread(target=one, args=(w,), daemon=True) for w in names]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)


def scene_threads(names):
    """진짜 `print` 로 여럿이 한꺼번에 — 끝 조건이 적은 그 장면."""
    def one(who):
        for i in range(LINES):
            print(say(who, i))
    run(one, names)


def scene_barrier(names):
    """엮인 판 — 본문을 다 쓴 뒤에야 개행이 나가게 빗장으로 엇갈림을 만든다."""
    gate = threading.Barrier(len(names))

    def one(who):
        for i in range(LINES):
            sys.stdout.write(say(who, i))
            gate.wait()                     # 본문끼리 먼저 만난다 — 여기가 그 엇갈림이다
            sys.stdout.write("\n")
            gate.wait()                     # 다음 줄이 앞줄의 개행을 앞지르지 않게
    run(one, names)


def mixed(lines, names):
    """섞인 줄 — **꼬리로 가른다**(머리말 ⚠ 시각 머리).

    성한 줄은 기대 한 줄로 끝나고, 그 앞에 본문이 또 들지 않는다. 앞은 시각 머리라 저장소
    형식이 무엇이든 본문을 안 든다. 붙은 줄은 꼬리가 성해도 앞에서 걸리고, 더 난 빈 줄은
    어느 꼬리와도 안 맞는다.
    """
    want = {say(w, i) for w in names for i in range(LINES)}
    width = len(say(names[0], 0))           # 기대 줄은 폭이 하나다 — 이 손이 지어서 안다
    return [ln for ln in lines
            if ln[-width:] not in want or BODY in ln[:-width]]


# ── 되돌린 사본 — 이빨 ────────────────────────────────────────────────────────

def broken_copy(base):
    """**고침을 걷은 사본** — 꼬리를 스레드가 같이 쓰던 그 꼴을 저장소 tee 위에 세운다.

    파일을 안 건드린다(몽키패치) — 되돌린 코드가 정말 빨강을 내는지만 본다.
    """
    class _SharedTail(base):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.tail = ""

        def write(self, s):
            with self.lock:
                if self.echo:
                    try:
                        self.console.write(s)
                    except Exception:      # noqa: BLE001
                        pass
                lines = (self.tail + s).split("\n")
                self.tail = lines.pop()
                for one in lines:
                    self.logger.log(self.level, one)
            return len(s)

    return _SharedTail


# ── 씨앗의 본보기 배관 — `--self` 가 이 위에서 돈다 ───────────────────────────

class _ThreadTail:
    """씨앗이 드는 본보기 tee — **꼬리를 스레드마다 든다.** 받는 저장소의 tee 도 이 꼴이다."""

    def __init__(self, console, logger, level, echo):
        self.console = console
        self.logger = logger
        self.level = level
        self.echo = echo
        self.tails = threading.local()      # 줄이 안 끝난 꼬리 — 스레드마다 제 것
        self.lock = threading.Lock()        # 꼬리가 아니라 **차례**의 것이다

    def write(self, s):
        with self.lock:
            if self.echo:
                try:
                    self.console.write(s)
                except Exception:          # noqa: BLE001
                    pass
            lines = (getattr(self.tails, "text", "") + s).split("\n")
            self.tails.text = lines.pop()
            for one in lines:
                self.logger.log(self.level, one)
        return len(s)

    def flush(self):
        if self.echo:
            try:
                self.console.flush()
            except Exception:              # noqa: BLE001
                pass

    def isatty(self):
        return False


class _StampOnce(logging.Formatter):
    """줄마다 시각 — 같은 초로 이어지는 줄은 같은 폭의 빈칸으로 잇는다.

    본보기에 시각을 붙이는 까닭은 **`--self` 가 꼬리 가름을 실제로 밟게** 하려는 것이다.
    머리가 없으면 머리말 ⚠ 의 그 손이 한 판도 안 걸린다.
    """

    def __init__(self):
        super().__init__()
        self.last = ""

    def format(self, record):
        stamp = datetime.fromtimestamp(record.created).isoformat(timespec="seconds")
        head = stamp if stamp != self.last else " " * len(stamp)
        self.last = stamp
        return f"{head} {record.getMessage()}"


def _self_open(path):
    """본보기 배선 — 저장소가 준 여는 손과 **같은 계약**: `(자리, 못 열었으면 사유)`."""
    path = Path(path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
    except OSError as exc:
        return path, f"{type(exc).__name__}: {exc}"
    handler.setFormatter(_StampOnce())
    logger = logging.getLogger("log_race_check.self")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    logging.raiseExceptions = False
    sys.stdout = _ThreadTail(sys.stdout, logger, logging.INFO, echo=False)
    sys.stderr = _ThreadTail(sys.stderr, logger, logging.ERROR, echo=False)
    return path, ""


# ── 배관 — 저장소가 주는 것을 한 자리에 모은다 ────────────────────────────────

class Plumbing:
    """어느 tee 를 갈아 끼우고 무엇으로 여나 — 저장소마다 다른 것은 이 한 벌뿐이다."""

    def __init__(self, name, holder, tee_attr, opener, into=None):
        self.name = name
        self.holder = holder
        self.tee_attr = tee_attr
        self.opener = opener
        self.into = into                    # (모듈, 이름) 또는 None

    @property
    def base(self):
        return getattr(self.holder, self.tee_attr)

    def swap(self, cls):
        setattr(self.holder, self.tee_attr, cls)

    def open(self, path):
        """그 자리에 tee 를 세운다 — 자리를 인자로 받나 설정에서 읽나로 갈린다."""
        if self.into is None:
            return self.opener(path)
        setattr(self.into[0], self.into[1], path)
        return self.opener()


def _module(name, what):
    try:
        return importlib.import_module(name)
    except Exception as exc:               # noqa: BLE001
        raise Unmeasured(f"[안 잼] {what} 의 모듈 {name!r} 을 못 들였다 — "
                         f"{type(exc).__name__}: {exc} · `--root` 로 나무 뿌리를 주는가") from exc


def _split(spec, count, what, shape):
    parts = spec.split(":")
    if len(parts) != count or not all(parts):
        raise Unmeasured(f"[안 잼] {what} 의 꼴이 아니다 — {spec!r} · 받는 꼴은 {shape}")
    return parts


def plumbing_of(args):
    """인자에서 배관 한 벌을 세운다 — 안 주면 그 자리에서 「못 쟀다」로 나간다."""
    if args.self_check:
        return Plumbing("씨앗 본보기", sys.modules[__name__], "_ThreadTail", _self_open)
    if not args.plumb:
        raise Unmeasured(
            "[안 잼] 배관을 안 줬다 — 어느 tee 를 갈아 끼우고 무엇으로 여나를 받아야 돈다.\n"
            "        `--plumb 모듈:tee:여는손` · 자리를 설정에서 읽는 여는 손이면 "
            "`--log-into 모듈:이름` 을 같이\n"
            "        · 모듈이 안 보이면 `--root <저장소>` · 배관 없이 돌려 보려면 `--self`")
    mod_name, tee_attr, open_attr = _split(args.plumb, 3, "`--plumb`", "`모듈:tee:여는손`")
    mod = _module(mod_name, "`--plumb`")
    for attr in (tee_attr, open_attr):
        if not hasattr(mod, attr):
            raise Unmeasured(f"[안 잼] {mod_name} 에 {attr!r} 이 없다 — 배관 이름을 다시 준다")
    into = None
    if args.log_into:
        into_mod, into_attr = _split(args.log_into, 2, "`--log-into`", "`모듈:이름`")
        into = (_module(into_mod, "`--log-into`"), into_attr)
    return Plumbing(args.plumb, mod, tee_attr, getattr(mod, open_attr), into)


# ── 한 장면을 실물 배선 위에서 돌린다 ─────────────────────────────────────────

def measured(plumb, tmp, scene, names, broken=False):
    """장면 하나를 **실물 배선** 위에서 돌리고 기록 파일의 줄들을 돌려준다."""
    where = tmp / "logs" / f"{scene.__name__}{'-broken' if broken else ''}.log"
    keep_out, keep_err, keep_tee = sys.stdout, sys.stderr, plumb.base
    logger = None
    try:
        if broken:
            plumb.swap(broken_copy(keep_tee))
        # 콘솔 쪽은 StringIO 가 받는다 — 판정 화면이 이 장면의 줄에 안 덮이게.
        sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
        path, why = plumb.open(where)
        if why:
            return None, why
        logger = getattr(sys.stdout, "logger", None)
        missing = [a for a in NEEDS if not hasattr(sys.stdout, a)]
        if missing:
            return None, ("여는 손이 세운 stdout 에 " + "·".join(missing)
                          + " 가 없다 — 머리말 「받는 저장소의 tee 가 들어야 하는 것」")
        scene(names)
    finally:
        sys.stdout, sys.stderr = keep_out, keep_err
        plumb.swap(keep_tee)
        for h in list(logger.handlers) if logger else ():
            h.close()
            logger.removeHandler(h)
    return path.read_text(encoding="utf-8").splitlines(), ""


def lines_of(plumb, tmp, scene, names, broken=False):
    got, why = measured(plumb, tmp, scene, names, broken)
    if why:
        STOP.append(f"{scene.__name__}: 기록을 못 열었다 — {why}")
        return []
    return got


def snapshot(where):
    return sorted(p.name for p in where.iterdir()) if where and where.exists() else []


# ── 판정 ──────────────────────────────────────────────────────────────────────

def parse(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    env = os.environ.get
    p.add_argument("--plumb", default=env("LOG_RACE_PLUMB"))
    p.add_argument("--log-into", default=env("LOG_RACE_LOG_INTO"))
    p.add_argument("--root", default=env("LOG_RACE_ROOT"))
    p.add_argument("--watch", default=env("LOG_RACE_WATCH"))
    p.add_argument("--self", dest="self_check", action="store_true")
    return p.parse_args(argv)


def main(argv):
    args = parse(argv)
    root = Path(args.root).resolve() if args.root else Path.cwd()
    sys.path.insert(0, str(root))
    plumb = plumbing_of(args)               # 배관이 없으면 여기서 2 로 나간다
    watch = (root / args.watch).resolve() if args.watch else None
    before = snapshot(watch)
    tmp = Path(tempfile.mkdtemp(prefix="log-race-"))

    print(f"[log_race_check] 콘솔 tee — 배관 {plumb.name} · 스레드 {THREADS} · 줄 {LINES}")

    print("\n① 엮인 판 — 본문끼리 만난 뒤 개행이 나간다 (빗장으로 만든 엇갈림)")
    two = NAMES[:2]
    got = lines_of(plumb, tmp, scene_barrier, two)
    show("줄 수", len(got), LINES * len(two))
    show("섞인 줄", len(mixed(got, two)), 0)

    print(f"\n② 스레드 {THREADS} — 진짜 print 로 한꺼번에 (끝 조건이 적은 자리)")
    got = lines_of(plumb, tmp, scene_threads, NAMES)
    show("줄 수", len(got), LINES * THREADS)
    show("섞인 줄", len(mixed(got, NAMES)), 0)

    print("\n③ 이빨 — 꼬리를 도로 공유한 사본은 빨강을 낸다")
    got = lines_of(plumb, tmp, scene_barrier, two, broken=True)
    bad = mixed(got, two)
    report("되돌린 사본의 엮인 판에서 줄이 섞인다", bool(bad),
           [f"섞인 줄 {len(bad)}개 — 되돌렸는데 안 섞였다면 이 검사가 결함을 못 재는 것이다"])
    if bad:
        edge(f"되돌린 사본이 낸 섞인 줄 {len(bad)}개 · 첫 줄: {bad[0][:60]!r}")
    got = lines_of(plumb, tmp, scene_threads, NAMES, broken=True)
    edge(f"되돌린 사본 · 한꺼번에 판에서 섞인 줄 {len(mixed(got, NAMES))}개 "
         "— 엇갈림이 인터프리터 몫이라 판정으로는 안 든다(0이어도 못 잰 것)")

    # --- 마감 -----------------------------------------------------------------
    if watch is None:
        edge("안 잰 것: 저장소 기록 자리에 남긴 것 — 잴 자리를 안 줬다(`--watch`)")
    else:
        left = snapshot(watch)
        report(f"기록 자리({watch.name})에 이 검사가 한 자도 안 남겼다", left == before,
               [f"시작 때 {before} · 끝 {left}"])
    if args.self_check:
        edge("안 잰 것: 어느 저장소의 배선 — `--self` 는 씨앗이 제 본보기 tee 를 잰다")
    for text in [
        "콘솔 쪽 줄 섞임 — tee 는 콘솔에 **조각 그대로** 되쏜다(그 자리는 안 바뀌었다). "
        "터미널에서 겹쳐 보이는 것은 여기가 안 든다",
        "잠금이 막히는 판 — 콘솔 파이프를 아무도 안 빨 때",
        "자정 회전 · 파일이 잠긴 판 · 죽었을 때 한 번 말하나 — 표준 핸들러와 그 저장소의 "
        "시끄러운 핸들러 몫이라 안 잰다",
        "stdout·stderr 두 tee 가 한 파일에 같이 쓸 때의 차례 — 여기는 stdout 하나만 쓴다",
        "시각 머리의 형식 — 꼬리로 가르므로 머리는 아예 안 본다(머리말 ⚠)",
    ]:
        edge(f"안 잰 것: {text}")

    shutil.rmtree(tmp, ignore_errors=True)

    print()
    if STOP:
        for row in STOP:
            print(f"⛔ 못 쟀다 — {row}")
        return EXIT_UNMEASURED
    if fails():
        print(f"❌ 어긋남 {len(fails())}건 — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"✅ 전부 통과 ({len(passes())}건) — 배관 {plumb.name} · 스레드 {THREADS} · "
          f"줄 {LINES} · 장면 둘(엮인 판 · 한꺼번에)과 이빨까지")
    return EXIT_OK


sys.exit(main(sys.argv[1:]))
