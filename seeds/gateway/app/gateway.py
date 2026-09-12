"""갈래 표와 자격 — 어디로 보내나 · 무엇으로 여나 · 얼마까지 받나.

⚠ **골든 씨앗이다** — 진본은 claude-config `seeds/gateway/` 이고, 새 프로젝트가 이 폴더를
  복사해 출발한다. 복사한 뒤 손댈 자리는 아래 `ENV_PREFIX` 하나와 갈래 표의 값이다 —
  나머지는 규격이라 고치면 짝(손잡이·난간·실측·곁말·검사)이 깨진다. 왜 이 값들인지의
  판정표는 claude-config 결정 0033 이 든다.

실측의 진본은 claude-config `posco/` 다. 여기 적힌 값은 셋 중 하나이고 어느 것인지는
줄마다 주석이 든다 — 사내 문서(파일명·행) · ENV-posco 실측 · 사내 문서 표 밖이라 실호출로
확인한 것. **한도는 변수로 연다** — 부딪히면 코드를 고치지 말고 변수부터 바꾸고, 값의
근거가 의심스러우면 프로브를 다시 돌린다.

계약별 어법은 `providers.py` 가 든다 — 이 파일은 「어디로」와 **「지금 거기 닿나」**까지다.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
from typing import NamedTuple
from urllib.parse import urlparse

# 환경변수 접두어 — **복사한 뒤 여기 한 자리만 바꾼다.** 같은 PC 에 형제 앱이 함께 뜨므로
# 접두어가 겹치면 늦게 뜬 쪽이 남의 손잡이를 문다. 저장소 이름의 머리글자가 관례다.
ENV_PREFIX = "APP"


def _env(name, default):
    """`{ENV_PREFIX}_{name}` — 손잡이는 전부 이 한 자리로 읽는다."""
    return os.environ.get(f"{ENV_PREFIX}_{name}", default)


# 앱이 제 손으로 여는 기록 폴더 — CLI 오류 증거(`providers._cli_evidence`)가 여기 앉는다.
LOGS_DIR = Path(_env("LOGS_DIR", "logs"))

# --- 담장 — 사내망 **안**으로 가나 **밖**으로 나가나.
# 주소로는 못 가른다: 사람이 아는 것은 「회사 거냐 내 거냐」지 호스트 이름이 아니다.
SITE_POSCO = "posco"
SITE_OUTSIDE = "outside"

# --- 키 묶음 — **한 키를 같이 쓰는 갈래들.** 회사 키는 사람마다 하나고 계약만
# 갈리므로(ENV-posco 22–23행), 갈래마다 따로 받으면 같은 키를 두 번 넣게 된다.
KEY_GROUP_POSCO = "posco"
KEY_GROUP_GEMINI = "gemini"
KEY_GROUP_ANTHROPIC = "anthropic"
# 로컬 CLI 갈래도 묶음을 갖는다 — **구독을 각자 것으로 가르는 자리다.** 빈 글자로 눌러
# 두면 화면이 키 칸 자체를 안 띄우고, 그러면 서버 PC 의 로그인 하나를 쓰는 사람 전원이
# 나눠 쓴다(atelier 실측 · 서버 문이 그 자리를 함께 막아야 한다 — 이 표만으로는 안 선다).
KEY_GROUP_CLAUDE_CLI = "claude-cli"

# 이 PC 에 깔린 실행파일 이름 — 부르는 자리는 `providers.py` 지만 「깔려 있나」를 여기서도
# 재야 해서(아래 `_local_verdict`) 이름의 진본을 이쪽에 둔다.
CLI_EXE = "claude"
# CLI 가 실제로 치는 API 끝점 — 「로컬」 갈래지만 CLI 는 이 PC 에서 떠서 **밖으로** 나간다.
# 이 길이 막힌 망에서는 깔려 있고 로그인돼 있어도 못 쓰므로, 로컬 갈래도 닿음 실측을 이
# 주소로 진다(atelier ADR 0167).
CLI_API_URL = "https://api.anthropic.com"

# --- 계약 — 어떤 말로 묻고 어떤 말로 받나. `providers.py` 가 이걸로 갈린다.
# ⚠ **갈래 이름과 남남이다.** 갈래는 「어디로 보내나」고 계약은 「어떤 말로 하나」다 —
#   한 계약을 두 갈래가 쓴다(회사 Gemini·내 키 Gemini · 회사 Claude·사외 Anthropic).
#   갈래 이름으로 계약을 판정하면 이름이 안 겹치는 갈래가 통째로 엉뚱한 데로 간다.
CONTRACT_ANTHROPIC = "anthropic"    # /v1/messages           · x-api-key
CONTRACT_OPENAI = "openai"          # /v1/responses          · Bearer
CONTRACT_GEMINI = "gemini"          # :streamGenerateContent · x-goog-api-key
CONTRACT_CLI = "cli"                # HTTP 아님 — 이 PC 의 실행파일을 파이프로

# --- 캐시 수명과 그것을 여는 베타 낱말.
# **고를 수 있는 것은 anthropic 계약뿐이다** — 나머지 둘은 접두사가 맞으면 자동이라
# 우리가 실을 표가 없다. 기본 수명 5분은 사람이 답을 쓰는 사이 식는다.
# 되돌리려면 `5m` 으로 둔다 — 그러면 필드도 낱말도 안 나간다(`providers._cache_ctl` 과 아래
# `_CACHE_BETAS` 가 **같은 손잡이**를 본다. 한쪽만 보면 「1시간을 열어 달라」고 말해 놓고
# 5분 봉투를 보내는 어긋난 요청이 되고, 이 게이트웨이는 모르는 낱말을 조용히 삼켜 안 운다).
CACHE_TTL = _env("CACHE_TTL", "1h")
CACHE_TTL_BETA = "extended-cache-ttl-2025-04-11"   # 1시간을 여는 낱말
OUTPUT_128K_BETA = "output-128k-2025-02-19"        # 128K 출력 상한을 여는 낱말
# 두 낱말 다 **사내 문서 머리 표에 없다**(ENV-posco 73–75행) — 흘려지면 상한은 옛 값이고
# 캐시 수명은 5분이다. 그래서 갈래마다 무엇을 싣나를 아래 표의 `betas` 칸이 든다.
_CACHE_BETAS = (CACHE_TTL_BETA,) if CACHE_TTL and CACHE_TTL != "5m" else ()

ANTHROPIC_VERSION = "2023-06-01"   # Claude-Posco.setting.md 14행 (기본값)

_GATEWAY = {
    # 회사 Claude — 주소·머리는 Claude-Posco.setting.md 10–14행 · 270–277행.
    # ⚠ **첫 항이 곧 기본이다** — 기본을 따로 적으면 목록과 어긋나고 어긋난 줄 아무도 모른다.
    #   순서의 뜻은 앱마다 다르다: 품질 우선이면 최상위가 앞(헬퍼), 비용 우선이면 싼 것이
    #   앞(아뜰리에). 여기는 최상위가 앞이다 — 복사한 앱이 제 뜻대로 돌린다.
    "anthropic": {"url": "http://aigpt.posco.net/gpgpta01-gpt/v1/messages",
                  # `claude-opus-5` 는 사내 「지원 모델」 표(같은 문서 279–284행) 밖인데
                  # 실제로 돈다 — 사용자 확인(ENV-posco 26–29행 · atelier 갈래 표).
                  "models": ("claude-opus-5",
                             "claude-opus-4.7",
                             "claude-sonnet-4.6"),
                  "site": SITE_POSCO, "label": "회사 Claude",
                  "key_group": KEY_GROUP_POSCO,
                  "contract": CONTRACT_ANTHROPIC,
                  "betas": (OUTPUT_128K_BETA, *_CACHE_BETAS)},
    # 회사 GPT — `/v1/responses` (OpenAI.-Posco.Setting.md 394–420행). 옛 문
    # (`/v1/chat/completions`)은 안 쓴다: 이 게이트웨이가 **다 만든 뒤 몰아 줘서**
    # 렌더가 길수록 사용자가 빈 화면을 본다(atelier #123 실측 · 커밋 2be4432).
    # 상한을 실을 이름이 이 계약만 다르다(같은 문서 415행).
    "openai":    {"url": "http://aigpt.posco.net/gpgpta01-gpt/v1/responses",
                  # 사내 문서 예시는 `gpt-5.2` 계열이고 이 둘은 표 밖 · 사용자 확인
                  # (atelier config.py 주석 · 커밋 2be4432). 최상위가 앞이다.
                  "models": ("gpt-5.6-sol", "gpt-5.6-terra"),
                  "site": SITE_POSCO, "label": "회사 GPT",
                  "key_group": KEY_GROUP_POSCO,
                  "contract": CONTRACT_OPENAI,
                  "max_tokens_field": "max_output_tokens"},
    # 회사 Gemini — 같은 호스트인데 **계약도 인증도 다르다.** P-GPT 가 구글 네이티브
    # 표면을 그대로 연다(Gemini-Posco.setting.md 12행 · 인증 17–18행).
    # `url` 은 **바닥 주소**다 — 이 계약만 경로에 모델 이름이 들어가서(providers 의
    # `_gemini_envelope`) 완성된 주소를 여기 적을 수가 없다.
    "gemini-posco": {"url": "http://aigpt.posco.net/gpgpta01-gpt",
                     # 등록 목록은 같은 문서 36–41행인데 「관리자 설정에 따라 다를 수
                     # 있다」고 저쪽이 든다 — `gemini-3.6-flash` 가 목록 밖 · 사용자
                     # 확인이다(atelier config.py 주석 · 커밋 2be4432).
                     "models": ("gemini-3.1-pro-preview", "gemini-3.6-flash"),
                     "site": SITE_POSCO, "label": "회사 Gemini",
                     "key_group": KEY_GROUP_POSCO,
                     "contract": CONTRACT_GEMINI},
    # --- 사내망 밖 — 같은 코드로 돌아야 한다. 게이트웨이가 아플 때
    # 제품이 서지 않게 하는 자리고, 집에서 시험하는 자리이기도 하다.
    "anthropic-api": {"url": "https://api.anthropic.com/v1/messages",
                      # 공개 모델 ID. 첫 항을 `claude-opus-5` 로 두는 까닭은 회사
                      # Claude 갈래의 기본과 **같은 모델**이라야 갈래를 바꿨을 때
                      # 품질 기준선이 비교되기 때문이다.
                      "models": ("claude-opus-5", "claude-sonnet-5"),
                      "site": SITE_OUTSIDE, "label": "내 키로 Anthropic",
                      "key_group": KEY_GROUP_ANTHROPIC,
                      "contract": CONTRACT_ANTHROPIC,
                      # ⚠ **128K 낱말을 안 싣는다 — 안 쟀다.** 이 문에 그 낱말이 아직
                      #   서는지 못 재 봤고, 아래 상한이 안전값이라 실을 값도 없다.
                      #   캐시 수명 낱말만 싣는다: 캐싱은 필수 규율이라(AI-prompt-helper 결정 0004)
                      #   두 자리가 같은 수명으로 돌아야 한다.
                      "betas": _CACHE_BETAS},
    # 내 키로 Gemini — 구글 직결. 회사 갈래와 **같은 계약**이라 코드가 하나다.
    # 첫 항이 기본이다 — 무료 키는 pro 미리보기의 할당량이 0 이라(429 · 2026-09-05 실측) flash 가 앞이다.
    "gemini":    {"url": "https://generativelanguage.googleapis.com",
                  "models": ("gemini-3.7-flash", "gemini-3.1-pro-preview"),
                  "site": SITE_OUTSIDE, "label": "내 키로 Gemini",
                  "key_group": KEY_GROUP_GEMINI,
                  "contract": CONTRACT_GEMINI},
    # 이 PC 에 깔린 claude CLI 를 그대로 부른다. 주소도 키도 없다 — 구독 로그인이 이미
    # 되어 있고 그 인증을 빌려 쓴다. 그래서 `local` 이 선다: **키가 없다고 드라이런으로
    # 떨어지면 안 되는 유일한 갈래다**(아래 `creds` 의 `dry_run`).
    # ⚠ 모델 이름이 게이트웨이 갈래와 다르다 — **별칭**이다. 별칭은 판을 안 고정하므로
    #   (CLI 도움말이 「alias for the latest model」로 적어 뒀다) 여기 판 번호를 안 적는다:
    #   적는 순간 낡고, 낡은 줄 아무도 모른다. 특정 판을 박으려면 화면 모델 칸에 정식
    #   이름을 직접 적는다. 위 게이트웨이 갈래들과 정반대다 — 저쪽은 회사가 등록한
    #   이름이라 목록이 곧 있는 것 전부다.
    # ⚠ **출력 상한을 실을 자리가 없다**(`providers._cli_once`) — `_MODEL_MAX_TOKENS` 에
    #   이 이름들을 안 적는 까닭이다. 안전값이 서지만 어차피 안 나간다.
    # ⚠ **별칭 셋은 atelier 갈래 표에서 그대로 가져왔다**(커밋 d93df1d). 첫 항만 이 앱의
    #   규율대로 최상위(`opus`)로 세웠고 뒤 둘의 서열은 **안 쟀다** — 별칭이 가리키는
    #   실물이 때마다 갈려 여기서 잴 수 있는 것이 아니다.
    "claude-cli": {"url": "", "local": True,
                   "models": ("opus", "sonnet", "fable"),
                   "site": SITE_OUTSIDE, "label": "이 PC 의 Claude 구독",
                   "key_group": KEY_GROUP_CLAUDE_CLI,
                   "contract": CONTRACT_CLI},
}
# 표에 안 적은 갈래가 쓰는 이름 — Anthropic·Gemini 가 이 이름을 쓴다.
_DEFAULT_MAX_TOKENS_FIELD = "max_tokens"
# 기본 갈래 — 요청이 안 고르면 이것으로 간다. 변수로 연다.
# ⚠ **모르는 이름은 뜰 때 죽는다.** 형제 하나는 옛 환경과의 호환으로 기본 행에 내리는데,
#   새로 출발하는 프로젝트에는 지킬 옛 환경이 없다 — 오타가 조용히 딴 갈래로 가는 것이
#   더 비싸다. 담장 검사(아래)는 이 판정 **뒤에** 선다.
DEFAULT_PROVIDER = _env("PROVIDER", next(iter(_GATEWAY))).lower()
if DEFAULT_PROVIDER not in _GATEWAY:
    raise RuntimeError(
        f"{ENV_PREFIX}_PROVIDER 가 모르는 갈래다: {DEFAULT_PROVIDER} — "
        f"있는 것은 {', '.join(_GATEWAY)} 이다")

# 담장 순서 — 표의 등장 순서를 따른다. 손으로 적으면 갈래를 더할 때 어긋난다.
SITES = tuple(dict.fromkeys(row["site"] for row in _GATEWAY.values()))


# --- 이 서버가 **여는** 담장 — 띄우는 사람이 선언한다 (atelier ADR 0253) -------------
#
# 비우면 다 연다. 회사에 띄울 때 `posco` 하나만 적으면 바깥 갈래(구글 직결 · 이 PC 구독)가
# 화면 목록에서 빠지고, 옛 브라우저 저장분이 그
# 갈래를 실어 와도 아래 `creds` 가 안 받는다 — 회사 자산이 회사 게이트웨이로만 간다.
# ⚠ **닿음 판정과 다른 축이다.** 저쪽은 열어 봐서 **잰 것**이고 이쪽은 띄운 사람이 **적은
#   것**이라 틀릴 자리가 없다. 그래서 닫힌 담장의 갈래는 **잠기는 것이 아니라 안 선다** —
#   잠긴 채 남겨 흐리게 두면 동료에게 「왜 회색이지」만 남는다. 잠금은 판정이 틀릴 수 있는
#   닿음 실측의 규율이다(아래 `why_unreachable`).
# ⚠ **모르는 이름은 뜰 때 죽인다** — 오타가 「다 연다」로 조용히 떨어지면 닫은 줄 알고 연다.
def _sites_allowed():
    names = tuple(dict.fromkeys(
        s.strip() for s in _env("SITES", "").split(",") if s.strip()))
    unknown = [s for s in names if s not in SITES]
    if unknown:
        raise RuntimeError(
            f"{ENV_PREFIX}_SITES 에 모르는 담장이 있다: {'·'.join(unknown)} — "
            f"고를 수 있는 것은 {'·'.join(SITES)} 이다")
    return names or SITES


SITES_ALLOWED = _sites_allowed()


def site_allowed(provider):
    """이 갈래의 담장을 이 서버가 여나 — 화면 목록과 요청 자격이 같은 한 번을 본다.

    모르는 갈래는 거짓이다 — 열린 담장에 속한다고 말할 근거가 없다.
    """
    row = _GATEWAY.get(provider)
    return row is not None and row["site"] in SITES_ALLOWED


# 기본 갈래가 닫힌 담장 것이면 **뜰 때 죽인다.** 안 그러면 갈래를 안 고른 요청이 닫은
# 담장으로 향하고, 그것을 `creds` 가 다시 기본 갈래로 내리는데 그 기본이 또 닫혀 있어
# **내림이 제자리를 돈다** — 기본이 없는 서버가 된다. 고칠 손잡이는 둘이다 —
# `{ENV_PREFIX}_PROVIDER` 를 열린 담장의 갈래로 두거나 `{ENV_PREFIX}_SITES` 를 넓힌다.
# ⚠ 이 검사는 기본 갈래의 이름 판정 **뒤**에 선다 — 앞에 서면 모르는 이름이 검사를 건너뛴다.
if not site_allowed(DEFAULT_PROVIDER):
    raise RuntimeError(
        f"기본 갈래 {DEFAULT_PROVIDER} 는 {_GATEWAY[DEFAULT_PROVIDER]['site']} 담장인데 "
        f"{ENV_PREFIX}_SITES 가 {'·'.join(SITES_ALLOWED)} 만 연다 — {ENV_PREFIX}_PROVIDER 를 "
        f"열린 담장의 갈래로 두거나 {ENV_PREFIX}_SITES 를 넓힌다")

# --- 키 묶음 → 그 묶음의 환경변수 후보. 앞에서부터 찾아 **처음 값이 있는 것**을 쓴다.
# ⚠ **읽는 자는 프로브들뿐이다**(`_check/gateway_probe.py` · `live_probe.py` · `stream_probe.py`). 서버는 아무에게도 키를
#   안 깔아 준다 — 로그인이 없어 「띄운 사람」과 「남」을 가를 재료가 없으므로, 깔면
#   띄운 사람의 키로 남이 마구 쓴다. 안 실어 온 요청은 드라이런이다.
_KEY_ENV = {
    # 회사 묶음이 둘을 보는 까닭 — 키는 하나인데 클라이언트마다 읽는 이름이 다르다
    # (ENV-posco 22–23행: 앱은 `ANTHROPIC_AUTH_TOKEN`, CLI 는 `ANTHROPIC_API_KEY`).
    KEY_GROUP_POSCO: ("ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY"),
    # 구글은 제 SDK 관례로 `GOOGLE_API_KEY` 를 쓴다 — 우리 이름이 앞, 별칭이 뒤다.
    KEY_GROUP_GEMINI: ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    # ⚠ **이 묶음은 환경변수를 안 읽는다 — 빈 것이 곧 규율이다.** 표준 이름
    #   (`ANTHROPIC_API_KEY`)이 회사 PC 에서는 **게이트웨이 키**라(ENV-posco 22–23행),
    #   읽으면 사내 키를 그대로 `api.anthropic.com` 으로 보낸다. 이 갈래의 키는
    #   프로브에 `--key` 로 손으로 준다.
    KEY_GROUP_ANTHROPIC: (),
    # `claude setup-token` 이 내주는 장기 토큰. CLI 가 이 이름을 읽고 **이 PC 의 로그인보다
    # 앞세운다**(atelier 2026-08-24 실측 — authMethod 가 claude.ai → oauth_token 으로
    # 뒤집힌다). 권한은 추론뿐이다 — 새도 그 이상은 못 한다.
    KEY_GROUP_CLAUDE_CLI: ("CLAUDE_CODE_OAUTH_TOKEN",),
}


def env_token(group):
    """키 묶음의 환경변수 기본값 — 없으면 빈 글자. **부르는 자는 프로브다**(위 ⚠)."""
    for name in _KEY_ENV.get(group, ()):
        if os.environ.get(name):
            return os.environ[name]
    return ""


# --- 닿나 — 한 번 재고 프로세스가 사는 동안 든다 (atelier ADR 0159 · 0167) ----------
#
# 집이냐 회사냐는 **PC 가 갈리지** 도중에 안 바뀐다. 매 요청마다 재면 화면이 그만큼 늦다.
#
# 캐시 열쇠가 갈래가 아니라 **끝점**인 까닭 — 회사 갈래 셋이 같은 호스트를 본다. 갈래마다
# 재면 죽은 망에서 같은 벽을 세 번 기다린다. 끝점 단위로 한 번만 재면 갈래가 늘어도 벽은
# 안 는다 — 「상태 문마다 나가는 요청이 갈래 수만큼 는다」는 걱정이 이 마디로 사라진다.
_reach = {}          # {(호스트, 포트, 스킴): (닿나, 못 닿은 까닭)}

# 두드리고 기다리는 시간. 살아 있으면 0.1초 안에 오므로 이 값은 **죽었을 때의 벽**이다.
# 화면이 뜰 때 한 번 무는 자리라, 끝점 둘이 다 죽으면 이 값의 두 배가 첫 화면에 얹힌다.
REACH_TIMEOUT_S = float(_env("REACH_TIMEOUT_S", "2"))

# 악수 실패의 까닭이 드는 칸 — **먼저 걸리는 것을 쓴다.** 닫힌 표라 여기 한 자리에 둔다.
# reason: OpenSSL 이 직접 거부한 자리 · verify_message: OS 검증기가 낸 문장 ·
# strerror: 인자 두 칸으로 선 여느 OSError 가지(곁의 `except OSError` 가 드는 그 칸)
SSL_WHY_FIELDS = ("reason", "verify_message", "strerror")


def _ssl_why(e):
    """악수가 왜 안 됐나 한 마디 — **드는 칸이 검증기마다 다르다.**

    OpenSSL 이 직접 거부하면 `reason` 이 찬다(`CERTIFICATE_VERIFY_FAILED`). 그런데 OS
    신뢰 저장소를 끼우는 갈래(윈도우·macOS)는 그 예외를 **손으로 짓는다** — 악수 동안
    검증을 끄고 OS 검증기로 따로 판정한 뒤 `ssl.SSLCertVerificationError(메시지)` 에
    `verify_message`·`verify_code` 만 달아 올린다. 거기엔 **`reason` 이 없다 — None 이
    아니라 속성 자체가 없다.**

    ⚠ 그래서 `e.reason` 을 바로 읽으면 그 갈래에서 `AttributeError` 가 나고, 그것이
      `except` 절 **안**에서 난 예외라 뒤의 `except OSError` 가 안 받아 `_probe` 밖으로
      나간다 — 까닭을 말하려던 자리가 **말 대신 넘어지고** `/api/status` 가 500 이 된다
      (atelier 실측 · ADR 0158). 하필 **검사 장비가 인증서를 갈아 끼우는 그 망**이 이
      함수가 있는 까닭이다.
    ⚠ **사내 PC 는 다 그 망을 낀다**(AI-prompt-helper 결정 0016) — 윈도우에서는
      손으로 지은 예외가 오는 그 갈래가 **오늘 걸리는 자리**다.
    ⚠ 리눅스에서는 안 보인다 — 거긴 OpenSSL 판정이 그대로 남아 `reason` 이 찬다.
      **깨지는 자리와 도는 자리가 갈린다.**

    OS 가 주는 `verify_message` 는 그 OS 가 낸 문장이라 오히려 사람 말에 가깝다 — 골라
    버리지 않고 그대로 싣는다(`why_unreachable` 의 「짐작하지 않는다」와 같은 결).
    """
    for field in SSL_WHY_FIELDS:
        why = getattr(e, field, None)
        if why:
            return str(why)
    # ⚠ 마지막이 `str(e)` 가 아닌 까닭 — `ssl.SSLError` 는 인자가 하나면 그것을 **튜플째**
    #   찍는다(`SSLError("끊겼다")` → `"('끊겼다',)"`). 괄호 안에 파이썬 문법이 새어 사람이
    #   읽을 자리가 아니게 된다. 곁의 `except OSError` 가 `str(e)` 로 족한 것은 저쪽은 그
    #   꼴이 아니어서다.
    return str(e.args[0]) if e.args else "SSL"


def _probe(url):
    """그 끝점과 실제로 말을 틀 수 있나 — (닿나, 까닭).

    ⚠ **이름이 풀리는 것과 닿는 것은 다른 명제다.** 이름만 보면 DNS 는 답하는데 길이 막힌
      망(분리망·VDI)에서 늘 참이 나오고, 화면은 반드시 실패할 갈래를 자신 있게 권한다.
      그래서 여는 데까지 간다.
    ⚠ **https 는 악수까지 간다.** TCP 만 열어 보면 검사 장비가 인증서를 갈아 끼워 악수에서
      죽는 자리를 못 잡는다 — 열리는 것과 말이 통하는 것이 또 다르다.
    """
    u = urlparse(url)
    host, secure = u.hostname, u.scheme == "https"
    port = u.port or (443 if secure else 80)
    try:
        with socket.create_connection((host, port), timeout=REACH_TIMEOUT_S) as sock:
            if not secure:
                return True, ""
            with ssl.create_default_context().wrap_socket(sock, server_hostname=host):
                return True, ""
    except socket.gaierror:
        return False, f"{host} 이름이 안 풀려요 — 이 망 안이 아니에요"
    except (socket.timeout, TimeoutError):
        return False, f"{host} 가 시간 안에 답을 안 해요 — 이 망에서 그리로 가는 길이 막혀 있어요"
    except ssl.SSLError as e:
        return False, (f"{host} 와 보안 악수가 안 돼요 — 인증서를 검사 장비가 갈아 "
                       f"끼웠을 수 있어요 ({_ssl_why(e)})")
    except OSError as e:
        return False, f"{host} 에 연결이 안 돼요 ({e.strerror or e})"


def _reach_of(url):
    """끝점 개방 판정 — 한 번 재고 프로세스가 사는 동안 든다(`_reach` 곁말).

    게이트웨이 갈래(`_verdict`)와 로컬 CLI 갈래(`_local_verdict`)가 같은 한 번을 나눠 쓴다 —
    따로 재면 죽은 망에서 같은 벽을 두 번 기다린다.
    """
    u = urlparse(url)
    key = (u.hostname, u.port, u.scheme)
    if key not in _reach:
        _reach[key] = _probe(url)
    return _reach[key]


# 이 PC 의 CLI 로그인 판정도 한 번 재고 든다 — 프로세스가 사는 동안 안 바뀐다.
# ⚠ 사람이 그 사이 로그인하면 낡는다. 그래서 판정이 **잠그기만** 하고, 여는 문은 눌렀을
#   때의 안내창(서버 문)이 든다 — 다시 띄우면 이 값도 다시 잰다.
# ⚠ **또렷한 답만 여기 든다.** 프로브가 넘어진 판은 「로그인됐다」가 아니라 **못 쟀다**라,
#   굳히면 그 판 서버가 죽을 때까지 안 재 본 답으로 산다. 못 잰 판은 그때그때 열어 주고
#   다음 물음에 다시 잰다(아래 `_local_verdict`).
_cli_auth = None

# CLI 는 프로세스를 띄우는 일이라 소켓 한 번보다 느리다 — 같은 손잡이에서 넉넉히 파생한다.
CLI_AUTH_TIMEOUT_S = REACH_TIMEOUT_S * 3


def _cli_logged_in(exe):
    """이 PC 의 CLI 가 로그인돼 있나 — (로그인됐나, 까닭) · **못 쟀으면 `None`.**

    ⚠ **값이 안 나간다.** 모델을 안 부르고 제 자격만 되읽는 자리다.
    ⚠ **못 재면 잠그지 않는다.** 프로브가 넘어졌다고 잠그면 멀쩡한 갈래가 막힌다 — 정말
      로그인이 없으면 눌렀을 때 안내창이 서므로 길이 막히지 않는다.
    ⚠ **그렇다고 「됐다」로 답하지도 않는다.** 열어 주는 것과 「재 봤더니 됐다」는 다른
      명제인데 한 값으로 내면 부르는 쪽이 못 가른다 — 그래서 굳어 버린다. 「아니다」(또렷)와
      「못 쟀다」(`None`)를 갈라 돌려주고, 무엇을 들고 있을지는 부르는 쪽이 정한다.
    """
    try:
        out = subprocess.run([exe, "auth", "status"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace",
                             timeout=CLI_AUTH_TIMEOUT_S)
        said = json.loads(out.stdout or "{}")
    except Exception:            # noqa: BLE001 — 넘어졌다·시간이 넘었다·JSON 이 아니다
        return None              #                 셋 다 「못 쟀다」다
    if said.get("loggedIn"):
        return True, ""
    return False, ("이 PC 의 Claude 가 로그인 안 돼 있어요 — 눌러서 로그인 창을 여세요, "
                   "또는 내 토큰을 넣으세요")


def _local_verdict(owner):
    """로컬 CLI 갈래 — 첫 물음은 **이 PC 에 있나**, 다음이 **밖으로 나가지나**다.

    「로컬」은 어디서 뜨나지 어디로 가나가 아니다 — CLI 는 이 PC 에서 떠서 밖
    (`CLI_API_URL`)으로 나가므로, 그 길이 막힌 망에서는 깔려 있고 로그인돼 있어도 못 쓴다.
    안 재면 **눌러야 죽는 갈래**가 되는 것처럼 보인다. 재는 자는 게이트웨이 갈래와 같은
    `_probe` 고, 막히면 그 까닭이 그대로 화면 잠금에 선다.

    주인 자리(루프백)는 이 PC 의 로그인이 곧 제 자격이라 로그인까지 잰다. 남의 자리는
    **자기 토큰을 실어 오므로** 이 PC 의 로그인 상태가 그 사람과 무관하다 — 재면 남의
    사정으로 남을 잠그게 된다.
    """
    global _cli_auth
    exe = shutil.which(CLI_EXE)
    if not exe:
        return False, f"이 PC 에서 {CLI_EXE} 를 못 찾았어요 — 깔거나 PATH 를 확인하세요"
    ok, why = _reach_of(CLI_API_URL)
    if not ok:
        return False, why
    if not owner:
        return True, ""
    if _cli_auth is None:
        said = _cli_logged_in(exe)
        if said is None:
            return True, ""      # **못 쟀다 — 잠그지도 굳히지도 않는다**(`_cli_auth` 곁말)
        _cli_auth = said
    return _cli_auth


def _verdict(provider, owner=False):
    """(닿나, 까닭) — `reachable` 과 `why_unreachable` 이 같은 한 번을 나눠 쓴다.

    ⚠ `owner` 는 **부른 사람이 이 서버 PC 앞에 앉아 있나**다. 로컬 갈래에서만 쓴다 — 그
      자리에서만 이 PC 의 로그인이 제 자격이 되기 때문이다.
    """
    row = _GATEWAY.get(provider)
    if row is None:
        return False, "모르는 갈래예요"
    if row.get("local"):
        return _local_verdict(owner)
    return _reach_of(row["url"])


def reachable(provider, owner=False):
    """이 갈래를 지금 이 PC 에서 부를 수 있나.

    ⚠ **재는 자리는 서버다.** 화면이 재게 두면 브라우저는 사내 호스트를 두드릴 길이 없어
      (교차 출처) 늘 「안 닿음」이 나온다 — 회사 PC 에서도 그렇다.
    로컬 갈래는 망만이 아니라 **깔려 있나**도 묻는다.
    """
    return _verdict(provider, owner)[0]


def why_unreachable(provider, owner=False):
    """왜 못 쓰나 — 화면이 잠근 자리에 이 말을 적는다.

    ⚠ **잠그되 목록에서 빼지 않는다.** 판정이 틀렸을 때 빠진 갈래는 사라진 줄도 모르고
      원인 찾기가 어렵다. 잠기면 까닭이 그 자리에 뜬다. (닫힌 담장은 이 규율 밖이다 —
      저건 잰 것이 아니라 적은 것이라 틀릴 자리가 없다 · `site_allowed` 곁말.)
    ⚠ **짐작하지 않는다.** 담장 이름으로 까닭을 지어내면 회사 PC 에서 회사 갈래가 막혔을
      때 「회사 PC 에서 쓰세요」 같은 거짓말이 나간다 — 실패한 그것을 그대로 말한다.
    """
    return _verdict(provider, owner)[1]


# --- 벽과 자 — 시간의 축. 돈의 축(캐시)과 갈린다.
# 사내 게이트웨이는 **요청부터의 절대 벽**에서 신호 없이 끊는다. 스트림이 열려도, 한 토큰도
# 안 나와도 같은 자리다 — 생성량과 무관하다(ENV-posco 「스트림 180초 컷」 실측 · 문서에 없다).
# ⚠ 앞단 HAProxy(300초 · gateway-front-haproxy.md)와 **다른 겹**이다. 값이 안 맞는다.
# ⚠ **저쪽의 시계지 우리 자가 아니다(AI-prompt-helper 결정 0017).** 이 값으로 요청을 스스로 끊지 않는다 —
#   끊으면 사람이 안 시킨 절단이고, 잘린 판은 stop 이 비어 이어받기가 못 붙는다(2026-09-07
#   실측: 문마다 이 값을 시한으로 걸어 두었더니 벽이 없는 CLI 구독 갈래의 ⑤ 까지 180초에
#   잘렸다). 여기서 파생하는 것은 하나, 아래 `WALL_MAX_TOKENS` 다.
GATEWAY_WALL_S = 180
# 사내 갈래의 **문 출력 상한 — 벽에서 역산한 값이다.** 실측(atelier 2026-08-14 · ENV-posco)이
# 말하는 것은 프리필은 시간을 거의 안 먹고 생성이 초당 34~58 토큰이라는 것이다:
#     180초 × 51 토큰/초 ≈ 9,177 토큰   ← 빨리 쓰는 판의 몫
# 상한을 벽 **안쪽**에 두면 절단이 계약(`max_tokens`)으로 와서 이어받기가 정확히 걸리고
# (`providers.stream_resumed`), 이어받은 바퀴도 다시 이 상한 안에서 끝난다. 벽에 닿게 두면
# stop 이 빈 채로 돌아와 「끝난 것」과 「잘린 것」을 영영 못 가른다.
# 4,000 인 까닭 — 보통 속도로 78초, 관측된 가장 느린 속도(34 토큰/초)로도 118초라 어느 쪽이든
# 벽 안이다. **낮게 틀리는 것이 안전하다.** 값과 역산은 atelier `config.TALK_MAX_TOKENS` 와 같다.
# ⚠ 바깥 갈래(내 키 · 이 PC 의 CLI)에는 벽이 없어 안 건다 — `creds` 가 담장(`site`)으로 가른다.
# ⚠ 생각이 길어 **시간이 침묵으로 가는 판**은 상한을 아무리 낮춰도 벽에 걸린다 — 그 판은
#   `providers.CUT_NO_SIGNAL` 로 기록에 남고 이어받기는 안 붙는다(닫힌 답에 걸면 지어낸다).
WALL_MAX_TOKENS = int(_env("WALL_MAX_TOKENS", "4000"))
# 소켓에 거는 자 — **침묵**을 잰다(총 시간이 아니다). 조각이 오면 되감긴다.
# 부르는 쪽이 `deadline` 을 주면 남은 예산과 이 값 중 먼저 오는 쪽이 선다(providers).
TIMEOUT_S = int(_env("TIMEOUT_S", "900"))

# --- 모델별 출력 상한 — 상한을 넘긴 값은 게이트웨이가 400 을 내고 스트림을 머리만
# 뱉은 뒤 끊는다. 그때 우리 손에는 빈 글자만 남아 **원인이 안 보인다.** 그래서 보내기 전에 이 표로 막는다.
_UNKNOWN_MAX_TOKENS = 64000          # 표에 없는 모델은 안전값
_MODEL_MAX_TOKENS = {
    # 사내 갈래의 값은 게이트웨이 실측(2026-08-12 · atelier `_MODEL_MAX_TOKENS`).
    "claude-sonnet-4.6": 128000,
    # ⚠ **이 둘은 안 쟀다** — 넘겨짚어 적었다가 틀리면 위 곁말대로 조용히 실패한다.
    #   실질 손해는 없다: 문 상한(`WALL_MAX_TOKENS`)이 어차피 먼저 온다.
    "claude-opus-4.7":   _UNKNOWN_MAX_TOKENS,
    "claude-opus-5":     _UNKNOWN_MAX_TOKENS,
    "gpt-5.6-terra":     128000,
    "gpt-5.6-sol":       128000,
    # Gemini 는 출력 상한이 절반 아래다.
    "gemini-3.6-flash":       65536,
    "gemini-3.1-pro-preview": 65536,
    "gemini-3.7-flash":       65536,
    # ⚠ **사외 Anthropic 갈래의 모델은 여기 없다 — 안 쟀다.** 공개 문서는 더 큰 값을
    #   들지만 이 저장소가 잰 것이 아니라, 안전값으로 떨어뜨린다. 재려면 값을 올려
    #   가며 한 번 부른다 — 400 이 오면 그 위가 벽이다.
}


# --- 입력 난간 — 봉투가 벽에 닿기 전에 서는 자 (AI-prompt-helper 결정 0024).
# 위 상한들이 **얼마를 받나**라면 이 값은 **얼마를 보내나**다. 넘겨 보내면 게이트웨이가
# 400 을 내거나, 모르는 것을 삼키는 성질대로 빈 채로 끊는다 — 뒤엣것이면
# `providers.CUT_NO_SIGNAL` 과 구별이 안 되고 원인이 입력 쪽이라 되부르기도 안 듣는다.
#
# **값은 모델 입력 한도에서 되짚는다.** 벽은 **토큰**인데 이 자는 **글자**라 환산이 낀다.
#
#     가장 낮은 벽 922,000토큰 × 1.0 자/토큰 ≈ 922,000자   →  난간 900,000자
#
# ⚠ **가장 낮은 벽이 사내 GPT 다.** Claude 갈래 넷(`claude-opus-5`·`4.7`·`sonnet-4.6`·
#   `sonnet-5`)은 1,000,000토큰이고, `gpt-5.6-sol` 의 922,000토큰이 그보다 낮다(값의 출처는
#   atelier `config.MAX_ENVELOPE_CHARS` 곁말 — 같은 게이트웨이·같은 모델 이름이다).
# ⚠ **환산비는 계약마다 다르고, 조이는 자는 「벽 × 비」가 가장 작은 모델이다** — 사내 실측
#   2026-09-09(`_check/live_probe.py ratio` · 한국어 산문 19,591자 · `_check/log/live-probe.log`):
#     anthropic(claude-opus-5) 1.26 자/토큰 · openai(gpt-5.6-sol) 2.06 · gemini 2.08
#   가장 낮은 벽은 GPT(922,000)지만 비가 2.06 이라 1.9M자까지 서고, Claude 는 벽이 1,000,000
#   이어도 비가 1.26 이라 **1.26M자에서 먼저 닿는다.** 되짚는 식은 「가장 낮은 벽 × 가장 낮은
#   비」가 아니라 **모델마다 벽 × 그 모델의 비를 내어 가장 작은 것**이다. 씨앗의 900,000 은 그
#   1.26M 아래에 남는 값이고, 그래서 그대로 둔다 — 낮게 틀리는 것이 안전하다.
# ⚠ **결이 다르면 비가 다르다** — 위 셋은 한국어 산문의 것이다. HTML·KB 가 섞인 봉투는 아뜰리에
#   표본 아홉이 1.17~2.09 였다. 제 봉투의 결로 다시 잰다 — 프로브가 파일을 받는다.
# ⚠ **안 쟀다.** ① 사내 게이트웨이가 모델 벽보다 **먼저** 세우는 입력 상한이 있나(사내 PC 몫)
#   ② `gpt-5.6-terra`·gemini 셋·CLI 별칭 셋의 입력 한도 — gemini 는 비(2.08)만 있고 벽이 없다.
MAX_ENVELOPE_CHARS = int(_env("MAX_ENVELOPE_CHARS", "900000"))


# 요청이 키를 실어 와도 안 보낸다 — 봉투 명세만 돌려준다.
# 판정은 요청마다 선다(아래 `creds`) — **프로세스가 쥔 사실은 이 강제 하나뿐**이라 여기
# 굳는 값도 그것 하나다. 서버가 키를 안 깔므로(`_KEY_ENV` 곁말) 「이 서버가 실호출인가」는
# 프로세스가 답할 수 있는 물음이 아니다 — 브라우저마다 다르다.
DRY_RUN_FORCED = _env("DRY_RUN", "") == "1"

# --- Gemini 갈래에 **생각을 흘려 달라고 요청한다** — 켜면 봉투에
# `generationConfig.thinkingConfig.includeThoughts` 가 실린다.
#
# ⚠ **품질 손잡이가 아니라 선을 살려 두는 손잡이다.** 앞단 HAProxy 의 `timeout server` 는
#   **조각 사이 무응답**을 재고 **조각이 오면 리셋된다**(실측 300초 ·
#   claude-config `posco/gateway-front-haproxy.md`). pro 모델이 생각에 들어가면 그동안 한
#   조각도 안 흘러 그 자를 넘기고, **구조 없는 HTML 504**(`The server didn't respond in
#   time.`)가 온다. SSE 를 심장박동으로 살리는 것이 이 제품의 표준 처방이고 **생각 조각이
#   곧 그 박동이다.** 시한을 늘리는 것이 아니라 선을 살려 두는 것이다.
# ⚠ **위 `WALL_MAX_TOKENS` 와 다른 겹이다** — 저쪽은 스트림이 흐르는 판의 180초 절대 벽을
#   상한으로 되짚은 값이고, 이쪽은 **아무 조각도 안 흐르는 판**의 자다. 상한을 아무리
#   낮춰도 침묵으로 가는 판은 못 막는다(AI-prompt-helper 결정 0017 이 「안 고치는 자리」로 적어 둔 그것).
# ⚠ **켠다고 생각을 더 시키는 것이 아니다** — 끈 판에도 `thoughtsTokenCount` 가 오므로
#   모델은 어차피 같은 만큼 생각한다. 켜는 것은 그 조각을 **흘려보내라**는 뜻이다.
# ⚠ **실측은 아뜰리에가 사내 게이트웨이에서 했다**(`_check/log/thinking-probe-runs.log` ·
#   2026-08-27). 400 이 안 오고 생각 조각이 실제로 흐르며, 켠 판이 선을 절반 시각에 연다 —
#   61,019자 봉투에서 6.1초→4.1초 · 81,193자에서 7.7초→3.9초. 「쓰기 전에 프로브로
#   잰다」는 규율을 그 실측으로 갈음한다(AI-prompt-helper 결정 0033).
# ⚠ **게이트웨이 제 504 와 다른 겹이다** — 저쪽이 낸 504 는 코드가 실려 오고 스트림 중이면
#   200 + `event: error` 로 온다. 우리가 받은 것은 코드 없는 HTML 이라 **게이트웨이가 낸
#   것이 아니다** — 이 가름이 없으면 다음 504 를 사내 오류 코드표에서 헛짚는다.
# ⚠ **죽는 판은 재현이 안 됐다** — 손잡이의 근거는 「504 를 없앤다」가 아니라 「기전이
#   실물에서 선다」까지다(아뜰리에 곁말 그대로). 켰으니 닫혔다고 읽지 않는다.
# ⚠ **상한을 걸 일이 생기면 `thinkingBudget` 이 아니라 `thinkingLevel` 이다**(gemini 3 ·
#   low·medium·high). 저쪽은 하위호환 낱말이고 **둘을 같이 실으면 400** 이다. 그리고 이
#   게이트웨이는 모르는 낱말을 조용히 삼키므로 그 낱말은 쓰기 전에 따로 재야 한다.
GEMINI_THOUGHTS = _env("GEMINI_THOUGHTS", "1") == "1"
# --- gemini 는 **생각 몫이 `maxOutputTokens` 안에 든다** — 사내 실측 2026-09-09(AI-prompt-helper #64):
# 상한 2,500 인 문이 `out=71 think=2401` 에서 잘렸다. 답 크기에 이 몫을 더해 싣는다
# (`providers._gm_envelope`). 켜고 끄는 것과 무관하다 — 끈 판에도 생각은 같은 만큼 한다.
# 값 — 그 판의 바퀴당 최대 생각 2,401 위로 여유를 둔 것. 180초 벽과의 셈: 가장 느리게 본 판(초당
# 57토큰)으로도 4,000+4,000 은 140초라 벽 안이다. ⚠ 생성 속도는 한 판 실측이다 — **안 쟀다**.
GEMINI_THINK_TOKENS = int(_env("GEMINI_THINK_TOKENS", "4000"))


def model_cap(model):
    """그 모델이 받는 출력 상한 — 표에 없으면 안전값. 봉투가 이 위로는 안 싣는다."""
    return _MODEL_MAX_TOKENS.get(model, _UNKNOWN_MAX_TOKENS)


class Creds(NamedTuple):
    """한 요청이 쓸 자격. `providers` 는 이것만 보고 부른다."""
    provider: str
    contract: str             # 어떤 말로 묻나 — 갈래 이름과 남남이다(위 CONTRACT_*)
    url: str
    token: str
    model: str
    max_tokens: int
    max_tokens_field: str     # 출력 상한을 실을 이름 — 갈래마다 다르다
    betas: tuple              # anthropic 계약에서만 실린다
    dry_run: bool
    local: bool               # 망 너머가 아니라 이 PC 에서 도나 — 자격 규율이 갈린다


def creds(provider=None, token=None, model=None, max_tokens=None):
    """요청이 실어 온 것 위에 갈래 기본을 깐다.

    ⚠ **키는 요청이 실어 온 것만 쓴다** — 서버 환경변수로 깔아 주지 않는다(위 `_KEY_ENV`
      곁말). 안 실어 오면 `dry_run` 이 서서 봉투 명세만 나간다 — 조용히 남의 키로
      새지 않는다.
    ⚠ **상한은 표가 집는다.** 모델을 바꿔 오면 상한도 그 모델 것이어야 한다(위 표의
      까닭). 부르는 쪽이 **더 낮은 값**을 주면 그것을 쓴다 — 높은 값은 안 받는다:
      난간을 부르는 쪽이 넘게 두면 난간이 아니다.
    ⚠ **모르는 갈래는 기본 갈래로 안 떨어뜨린다 — 선다.** 떨어뜨리면 사외를 고른
      요청이 **말없이 사내 게이트웨이로** 가고(또는 그 반대로) 기록에는 고른 이름이
      찍힌다 — 담장이 있으나 마나가 된다. atelier 는 떨어뜨리는데, 저쪽은 갈래가
      프로세스 설정이고 이쪽은 **요청마다 사람이 고르는 값**이라 규율이 갈린다.
    ⚠ **닫힌 담장의 갈래는 다르다 — 선 대신 내린다.** 이름을 아는데 이 서버가 안 여는
      것이라, 대개 옛 브라우저 저장분이다. 기본 갈래로 내리되 **키·모델도 함께 비운다**:
      셋이 한 담장에서 온 한 벌이라, 키는 다른 묶음 것이고 모델은 그 갈래만 아는 이름이다.
      비운 키가 아래 `dry_run` 을 세워 **어디로도 안 나간다** — 위 ⚠ 가 막으려던
      「말없이 사내 게이트웨이로 간다」가 여기서는 안 난다.
    """
    provider = (provider or DEFAULT_PROVIDER).lower()
    if provider not in _GATEWAY:
        raise ValueError(f"모르는 갈래다 — {provider} (있는 것: {', '.join(_GATEWAY)})")
    if not site_allowed(provider):
        provider, token, model = DEFAULT_PROVIDER, "", None
    row = _GATEWAY[provider]
    model = model or row["models"][0]
    cap = _MODEL_MAX_TOKENS.get(model, _UNKNOWN_MAX_TOKENS)
    if row["site"] == SITE_POSCO:
        # 벽 안쪽으로 — 절단이 계약으로 오게(`WALL_MAX_TOKENS` 곁말 · AI-prompt-helper 결정 0017)
        cap = min(cap, WALL_MAX_TOKENS)
    token = token or ""
    return Creds(
        provider=provider,
        contract=row["contract"],
        url=row["url"],
        token=token,
        model=model,
        max_tokens=min(cap, max_tokens) if max_tokens else cap,
        max_tokens_field=row.get("max_tokens_field", _DEFAULT_MAX_TOKENS_FIELD),
        betas=tuple(row.get("betas", ())),
        # 로컬 갈래는 **키가 없는 것이 정상이다** — 없다고 드라이런으로 떨어뜨리면 그
        # 갈래를 아예 못 쓴다. 자격은 이 PC 의 구독 로그인이 지고, 그 자리를 앞자리로
        # 좁히는 것은 서버의 자격 문이 든다.
        dry_run=DRY_RUN_FORCED or not (token or row.get("local")),
        local=bool(row.get("local")))
