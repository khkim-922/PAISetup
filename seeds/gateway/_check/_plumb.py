"""배관을 무는 자 — 검사 다섯이 앱의 배관 모듈을 **선언에서** 문다.

이 파일은 혼자 안 돈다(`--self-check` 빼고). 검사가 불러 쓰는 재료다.

**왜 이 파일이 있나.** 게이트웨이 검사 다섯은 사본으로 형제 저장소에 산다. 사본은 진본과
글자가 같아야 `borrowed_check.py` 가 초록인데, 검사가 `from app import gateway` 를 박고
있으면 배관을 다른 이름으로 두는 저장소는 받는 순간 그 줄을 손으로 고쳐야 하고, 고치는
순간 어긋남으로 뜬다. 그래서 **갈리는 것을 검사 밖으로 뺀다** — 좌표는 `gateway.conf` 가
들고 검사는 이 자를 통해 문다(claude-config #26 갈래 1 · 결정 0033 「앱은 갈려도 된다」).

**갈리는 자리가 몇인지 세고 들어왔다**(실측 2026-09-13 · 그 트리 지문은 보고가 든다). 검사
다섯이 코드로 무는 이름은 **스물여덟**인데(점으로 무는 자 스물일곱 · `getattr` 로 무는 자
하나) 형제 사이에서 **이름이 갈리는 것은 셋뿐**이다 — 나머지 스물넷은 세 저장소가 같은
이름으로 든다. 그래서 이 자의 몸통은 매핑표가 아니라 **모듈 이름 하나**이고, `[where]` 는
예외를 적는 자리로 남는다. 예외가 열을 넘어가기 시작하면 그때는 이 길이 아니라 배관을
맞추는 길이다(#26 갈래 2).

**어떻게 주나.**

    [plumb]     module = app.gateway        # 배관이 사는 모듈 — 스물넷이 여기서 나온다
                providers = app.providers   # 갈래별 말하기가 사는 모듈
    [where]     LOGS_DIR = app.config:LOGS_DIR   # `module` 이 안 드는 자리만 · `모듈:이름`
    [values]    ENV_PREFIX = ATELIER             # 속성이 **아예 없는** 자리 · 좌표가 아니라 값
    [no_handle] PROVIDER = 기본 갈래를 상수로 둔다   # **손잡이가 아예 없는** 자리 · 값이 까닭이다

선언이 없으면 씨앗 기본값(`app.gateway` · `app.providers`)으로 돈다 — 씨앗 저장소 자신과
배관 이름이 같은 형제는 선언을 안 채워도 그대로 돈다.

    from _plumb import gateway, providers      # 안 갈리는 스물넷은 이대로
    from _plumb import get, put, slot          # 갈릴 수 있는 셋은 이 손으로
    from _plumb import NO_HANDLE               # 그 앱이 안 여는 환경변수 손잡이

  · `slot(이름)` — `(모듈, 속성이름)`. 값을 읽고 쓰는 자리가 아니라 **좌표가 필요할 때**
  · `get(이름)` · `put(이름, 값)` — 검사가 배관 값을 읽거나 갈아 끼울 때
  · 셋 다 선언이 「없다」고 한 자리에서는 `Missing` 을 던진다 — 부르는 검사가 그것을
    「못 쟀다」(2)로 옮긴다. **빨강이 아니다**: 안 잰 것이지 어긋난 것이 아니다
  · `NO_HANDLE` — `{손잡이 이름: 까닭}`. 접두어를 뗀 이름이 칸 이름이고 값이 까닭이다
    (`PROVIDER` → `{접두어}_PROVIDER`). 비었으면 **손잡이가 있다**가 기본이다

⚠ **`[no_handle]` 은 `[values]` 와 층이 다르다.** 저쪽은 「배관에 그 **속성**이 없다」이고
  이쪽은 「그 속성을 밖에서 바꾸는 **환경변수**가 없다」다 — 기본 갈래를 상수로 두는 앱은
  `DEFAULT_PROVIDER` 속성을 멀쩡히 들고 있으므로 `[values]` 에 적으면 거짓말이 된다. 그래서
  이 절은 좌표도 값도 아니라 **까닭**을 든다: 그 까닭이 검사의 「뺀 자리」 줄에 그대로 찍힌다.

⚠ **이 절은 사람의 선언이라 어느 검사도 실측으로 되뽑지 않는다.** 손잡이가 있는데 없다고
  적은 판은 안 걸린다 — 되뽑으려면 그 손잡이가 서나를 재야 하는데 그것이 곧 뺀 판정 자체라,
  뺀 자리를 뺐는지 재는 자가 되어 제자리를 돈다. 적는 사람이 드는 책임이다.

⚠ **이 자가 배관을 고르지 검사가 고르지 않는다.** 검사 안에 `app.gateway` 를 다시 적으면
  그 검사만 조용히 씨앗 이름에 묶여, 받은 저장소에서 초록인 채로 **남의 모듈을 잰다.**

⚠ **`--self-check` 는 재는 자가 곧 재이는 것이다.** 선언이 빈 저장소에서는 `[where]`·
  `[values]` 가 한 줄도 안 돌아 「옮긴 자리가 정말 따라가나」가 **안 재진 채로 초록**이 된다.
  그래서 임시 트리에 배관을 지어 옮김·이름갈림·없음 셋을 실제로 밟는다.

    python -X utf8 _check/_plumb.py --self-check
    python -X utf8 _check/_plumb.py --show [<트리>]   # 그 트리의 선언이 무엇으로 풀리나

**안 재는 것** — 배관 모듈 **안**이 성한가(그것은 배관을 무는 검사 다섯의 몫이다) · 선언에
적힌 모듈이 실제로 임포트되나는 `--show` 가 부를 때만 본다.
"""
import argparse
import configparser
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONF = "gateway.conf"

# 씨앗 기본값 — 선언이 없거나 그 칸이 비면 이것으로 돈다.
SEED_MODULE = "app.gateway"
SEED_PROVIDERS = "app.providers"


class Missing(LookupError):
    """선언이 「이 저장소엔 그 자리가 없다」고 한 것. 어긋남이 아니라 **안 잰 것**이다."""


# ── 선언을 읽는다 ─────────────────────────────────────────────────────────────

def read(conf_dir=None):
    """선언 한 장을 읽어 `(plumb, where, values, no_handle)` 네 칸을 돌려준다.

    없으면 빈 칸 넷 — 선언이 없는 저장소는 「씨앗 기본값 · 옮긴 자리 없음 · 없는 속성 없음 ·
    **손잡이는 다 있다**」로 돈다. 마지막이 빈 것이 곧 「셋을 다 재라」는 뜻이다.
    """
    cp = configparser.ConfigParser(interpolation=None, delimiters=("=",))
    cp.optionxform = str            # 속성 이름은 대소문자가 뜻이다 — `LOGS_DIR` ≠ `logs_dir`
    path = Path(conf_dir or HERE) / CONF
    if path.exists():
        cp.read(path, encoding="utf-8")
    return (dict(cp["plumb"]) if cp.has_section("plumb") else {},
            dict(cp["where"]) if cp.has_section("where") else {},
            dict(cp["values"]) if cp.has_section("values") else {},
            dict(cp["no_handle"]) if cp.has_section("no_handle") else {})


class Plumbing:
    """선언 한 장이 풀린 꼴 — 모듈 둘과 예외 몇."""

    def __init__(self, conf_dir=None, root=None):
        plumb, where, values, no_handle = read(conf_dir)
        self.root = Path(root or Path(conf_dir or HERE).parent).resolve()
        if str(self.root) not in sys.path:
            sys.path.insert(0, str(self.root))
        self.module_name = plumb.get("module") or SEED_MODULE
        self.providers_name = plumb.get("providers") or SEED_PROVIDERS
        self.where = where
        self.values = values
        # ⚠ **좌표가 아니라 까닭이 든 칸이다** — 값을 풀지 않고 그대로 든다. 부르는 검사가
        #   그 글자를 「뺀 자리」 줄에 찍으므로, 여기서 손대면 앱이 적은 까닭이 갈린다.
        self.no_handle = no_handle
        self.gateway = importlib.import_module(self.module_name)
        self.providers = importlib.import_module(self.providers_name)

    def slot(self, name):
        """`(모듈, 속성이름)` — 선언이 옮겼으면 그리로, 없다고 하면 `Missing`."""
        if name in self.values:
            raise Missing(f"`{name}` 은 이 저장소 배관에 속성으로 없다 — 선언 `[values]` 가 "
                          f"값을 든다: {self.values[name]!r}")
        coord = self.where.get(name)
        if not coord:
            return self.gateway, name
        mod_name, _, attr = coord.partition(":")
        if not mod_name.strip() or not attr.strip():
            raise Missing(f"선언 `[where] {name}` 의 꼴이 `모듈:이름` 이 아니다: {coord!r}")
        return importlib.import_module(mod_name.strip()), attr.strip()

    def get(self, name):
        """배관이 든 값. 속성이 없는 저장소면 선언 `[values]` 의 값이 대신 선다."""
        if name in self.values:
            return self.values[name]
        mod, attr = self.slot(name)
        try:
            return getattr(mod, attr)
        except AttributeError as exc:
            raise Missing(f"`{mod.__name__}:{attr}` 가 없다 — 선언 `[where] {name}` 을 "
                          f"이 저장소 자리로 고치거나, 속성이 없으면 `[values]` 로 옮겨라") from exc

    def put(self, name, value):
        """배관 값을 갈아 끼운다 — 검사가 제 임시 자리로 돌릴 때."""
        mod, attr = self.slot(name)
        setattr(mod, attr, value)

    @property
    def label(self):
        return (self.module_name if self.module_name == self.providers_name
                else f"{self.module_name} · {self.providers_name}")


# ── 검사가 무는 자리 ──────────────────────────────────────────────────────────

_P = Plumbing()

gateway = _P.gateway
providers = _P.providers
slot = _P.slot
get = _P.get
put = _P.put
PLUMB = _P.label
# 모듈 **이름** — 자식 프로세스로 배관을 넘길 때 쓴다. 자식은 이 폴더가 경로에 없어
# `_plumb` 을 못 무므로, 이름을 인자로 받아 제 손으로 `import_module` 한다.
MODULE = _P.module_name
PROVIDERS_MODULE = _P.providers_name
# 이 앱이 **안 여는** 환경변수 손잡이 — `{접두어를 뗀 이름: 까닭}`. 비었으면 다 여는 것으로
# 본다(그래서 선언을 안 채운 형제는 종전 그대로 다 재진다).
NO_HANDLE = _P.no_handle


# ── `--self-check` · `--show` ────────────────────────────────────────────────

_FAKE_APP = '''
CLI_EXE = "claude"
ENV_PREFIX = "SEED"
LOGS_DIR = "안 옮긴 자리"
def env_token(group):
    return "씨앗 이름"
'''
_FAKE_SIDE = '''
LOGS_DIR = "옮긴 자리"
def _env_token(group):
    return "밑줄 붙은 이름"
'''
_FAKE_PROVIDERS = 'def stream_once(*a, **k):\n    return "말했다", None\n'


def _self_check():
    import shutil
    import tempfile

    from _verdict import EXIT_MISMATCH, EXIT_OK, edge, fails, passes, show

    tmp = Path(tempfile.mkdtemp(prefix="plumb-self-")).resolve()

    def fresh(conf_dir):
        """임시 트리의 배관으로 새로 푼다.

        ⚠ **먼저 `sys.modules` 에서 `app*` 을 걷어낸다.** 이 파일은 무는 순간 이 저장소의
          진짜 배관을 이미 올려 뒀다 — 안 걷으면 임시 트리를 가리켜 놓고 **진짜 모듈을
          되읽어** 자리 옮김이 안 재진 채 초록이 된다.
        """
        for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            sys.modules.pop(name, None)
        return Plumbing(conf_dir, tmp)

    try:
        app = tmp / "app"
        app.mkdir()
        (app / "__init__.py").write_text("", encoding="utf-8")
        (app / "gateway.py").write_text(_FAKE_APP, encoding="utf-8")
        (app / "config.py").write_text(_FAKE_SIDE, encoding="utf-8")
        (app / "providers.py").write_text(_FAKE_PROVIDERS, encoding="utf-8")
        conf_dir = tmp / "_check"
        conf_dir.mkdir()

        print("[_plumb --self-check] 임시 트리에 배관을 지어 선언이 정말 따라가나 — "
              f"{tmp}")

        # ① 선언이 없으면 씨앗 기본값으로 돈다
        (conf_dir / CONF).write_text("", encoding="utf-8")
        p = fresh(conf_dir)
        show("① 선언이 비면 씨앗 기본값이 선다", p.module_name, SEED_MODULE)
        show("① 그 배관에서 안 갈린 이름이 나온다", p.get("CLI_EXE"), "claude")

        # ② 모듈 이름을 갈면 그리로 간다 — 갈래 1 의 이빨
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.config\nproviders = app.providers\n", encoding="utf-8")
        p = fresh(conf_dir)
        show("② 모듈을 갈면 그 모듈이 선다", p.module_name, "app.config")
        show("② 값도 그 모듈에서 나온다", p.get("LOGS_DIR"), "옮긴 자리")
        show("② 갈래별 말하기는 따로 선다", p.providers.stream_once()[0], "말했다")

        # ③ 한 자리만 옮긴다 — 나머지는 `module` 이 계속 든다
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n[where]\nLOGS_DIR = app.config:LOGS_DIR\n",
            encoding="utf-8")
        p = fresh(conf_dir)
        show("③ 옮긴 자리는 옮긴 모듈에서 나온다", p.get("LOGS_DIR"), "옮긴 자리")
        show("③ 안 옮긴 자리는 그대로다 (음성 대조)", p.get("CLI_EXE"), "claude")

        # ④ 이름까지 갈린 자리
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n[where]\nenv_token = app.config:_env_token\n",
            encoding="utf-8")
        p = fresh(conf_dir)
        show("④ 이름이 갈린 자리는 그 이름으로 나온다", p.get("env_token")(None),
             "밑줄 붙은 이름")

        # ⑤ 갈아 끼우기가 옮긴 자리를 따라간다 — `put` 이 씨앗 모듈에 떨어지면 검사가
        #    제 임시 폴더 대신 **그 PC 의 진짜 자리**를 더럽힌다
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n[where]\nLOGS_DIR = app.config:LOGS_DIR\n",
            encoding="utf-8")
        p = fresh(conf_dir)
        p.put("LOGS_DIR", "검사가 앉힌 자리")
        show("⑤ 갈아 끼운 값이 옮긴 모듈에 앉는다", p.get("LOGS_DIR"), "검사가 앉힌 자리")
        show("⑤ 씨앗 모듈은 안 건드려졌다 (음성 대조)",
             importlib.import_module(SEED_MODULE).LOGS_DIR, "안 옮긴 자리")

        # ⑥ 속성이 아예 없는 자리 — 값이 대신 서고, 좌표를 물으면 `Missing`
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n[values]\nENV_PREFIX = 아뜰리에\n",
            encoding="utf-8")
        p = fresh(conf_dir)
        show("⑥ 속성이 없는 자리는 선언의 값이 선다", p.get("ENV_PREFIX"), "아뜰리에")
        try:
            p.slot("ENV_PREFIX")
            got = "안 던졌다"
        except Missing:
            got = "Missing"
        show("⑥ 그 자리의 **좌표**를 물으면 못 쟀다로 간다", got, "Missing")

        # ⑦ 선언이 엉뚱한 자리를 가리키면 조용히 안 넘어간다
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n[where]\nLOGS_DIR = app.config:없는이름\n",
            encoding="utf-8")
        p = fresh(conf_dir)
        try:
            p.get("LOGS_DIR")
            got = "안 던졌다"
        except Missing:
            got = "Missing"
        show("⑦ 없는 자리를 가리킨 선언은 못 쟀다로 간다", got, "Missing")

        # ⑧ 손잡이가 아예 없는 자리 — 좌표도 값도 아니라 **까닭**이 선다. 이 칸이 안 읽히면
        #    선언을 적은 앱에서 검사가 그대로 빨강이라, 「없다」가 조용히 어긋남으로 읽힌다.
        (conf_dir / CONF).write_text(
            "[plumb]\nmodule = app.gateway\n"
            "[no_handle]\nPROVIDER = 기본 갈래를 상수로 둔다\n", encoding="utf-8")
        p = fresh(conf_dir)
        show("⑧ 손잡이가 없다는 선언은 까닭을 들고 선다",
             p.no_handle.get("PROVIDER"), "기본 갈래를 상수로 둔다")
        show("⑧ 안 적은 손잡이는 없다고 안 한다 (음성 대조)", p.no_handle.get("SITES"), None)
        show("⑧ 손잡이 선언이 좌표를 흔들지 않는다 (음성 대조)", p.get("CLI_EXE"), "claude")
    finally:
        for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
            sys.modules.pop(name, None)
        if str(tmp) in sys.path:
            sys.path.remove(str(tmp))
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    edge("잰 범위 — **선언이 좌표를 옮기나**뿐이다. 배관 모듈 **안**이 성한가는 이 자가 "
         "한 자도 안 잰다 — 그것은 이 배관을 무는 검사 다섯의 몫이다")
    edge("안 잰 것 — 이 저장소의 실물 선언(`gateway.conf`)이 무엇으로 풀리나. "
         "그것은 `--show` 가 든다")
    edge("안 잰 것 — `[no_handle]` 의 선언이 **참인가**. 손잡이가 있는데 없다고 적은 판은 "
         "여기도 부르는 검사도 안 잡는다 — 적는 사람이 드는 책임이다")
    if fails():
        print(f"\n❌ 어긋났다 ({len(fails())}건) — {' · '.join(fails())}")
        return EXIT_MISMATCH
    print(f"\n✅ 선언이 좌표를 옮긴다 — 판정 {len(passes())}건 (기본값 · 모듈 갈이 · "
          f"한 자리 옮김 · 이름 갈림 · 갈아 끼우기 · 없는 자리 · 엉뚱한 자리 · 없는 손잡이)")
    return EXIT_OK


def _show(root):
    root = Path(root).resolve()
    p = Plumbing(root / "_check", root)
    print(f"나무 {root}")
    print(f"  배관      {p.module_name}  ←  {p.gateway.__file__}")
    print(f"  말하기    {p.providers_name}  ←  {p.providers.__file__}")
    print(f"  옮긴 자리 {p.where or '없다 — 배관이 다 든다'}")
    print(f"  값으로 든 자리 {p.values or '없다'}")
    print(f"  손잡이 없는 자리 {p.no_handle or '없다 — 손잡이가 다 있다고 본다'}")
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--show", nargs="?", const=str(HERE.parent), default=None)
    args = ap.parse_args()
    if args.self_check:
        sys.exit(_self_check())
    if args.show is not None:
        sys.exit(_show(args.show))
    ap.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
