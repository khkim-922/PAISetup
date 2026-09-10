"""계약 넷 어댑터 — 능력 넷만 든다 (AI-prompt-helper 결정 0006).

⚠ **골든 씨앗이다** — 진본은 claude-config `seeds/gateway/` 이고, 새 프로젝트가 이 폴더를
  복사해 출발한다. 몸통은 실측이 있는 쪽에서 왔다 — 씀씀이·이음매·생각 조각은 아뜰리에가
  사내 게이트웨이에서 잰 것이고, 거절·빈손·캐시 경계 셈은 헬퍼가 그 사고를 보고 일반화한
  것이다. 어느 자리가 어느 쪽에서 왔고 왜인지는 claude-config 결정 0033 의 판정표가 든다.

  - Anthropic: `/v1/messages`            · x-api-key      · `content_block_delta`
  - OpenAI:    `/v1/responses`           · Bearer         · `response.output_text.delta`
  - Gemini:    `…:streamGenerateContent` · x-goog-api-key · `candidates[].content.parts`
  - CLI:       **HTTP 가 아니다** — 이 PC 의 `claude` 를 파이프로 부르고 구독 인증을
    빌린다. 주소도 키 머리도 없어 봉투 꼴이 저 셋과 다르다(`CliEnvelope`).

능력 넷 — 글자 스트림 · 캐시 경계 · 씀씀이 보고 · 이어받기. 도구 호출·첨부는 안 든다 —
그것은 앱이 제 위에 얹는다(아뜰리에의 도구 루프가 그 본이다). 부르는 쪽이 계약을 몰라도 되게 여기서 한 번 갈라
`(글자, stop_reason)` 로 통일해 돌려주고, stop_reason 은 **Anthropic 어휘**로 맞춘다
(`max_tokens` · `end_turn` · 그 밖은 그대로) — 그래야 이어받기가 계약 셋에 다 걸린다.

⚠ **짓기와 보내기를 가른다.** 봉투는 순수 함수(`envelope`)가 짓고 보내는 함수는 그것을
  쓴다 — 키가 없으면 짓기까지만 하고 명세를 돌려준다(드라이런).
"""
import http.client
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import NamedTuple

from . import gateway

# 이어받기 바퀴 상한 — 끊김이 되풀이되면 한 회가 통째로 3분이라(180초 벽) 크게 두면
# 사람이 화면 앞에서 십 분을 기다린다. 변수로 연다 — 되풀이 끊김이 사고로 났을 때 재기동만으로
# 바퀴를 줄일 수 있게.
MAX_CONTINUE = int(gateway._env("MAX_CONTINUE", "5"))
# 키 없이 돌아온 판의 종료 사유 — 계약 어휘가 아니라 **우리 낱말**이라 갈리게 둔다.
# 이어받기 목록에 없으므로 드라이런은 바퀴를 안 돈다.
STOP_DRY_RUN = "dry_run"
# 드라이런 명세에 찍을 본문 길이 — 고정 층이 실리면 봉투가 수만 자다.
SPEC_BODY_CAP = 2000


# ---------- 봉투 — 짓는 자리 ----------

class Envelope(NamedTuple):
    """보낼 것 한 벌. **키 자리는 비어 있다** — 채우는 자는 `_sealed` 하나다."""
    url: str
    headers: dict        # 키 머리도 여기 서되 값이 빈 글자다
    body: dict
    key_header: str      # 그 빈 자리의 이름
    key_fmt: str         # 토큰이 그 자리에 앉는 꼴 — "{}" 또는 "Bearer {}"
    # 출력 상한이 **실제로 앉은 자리**. 짓는 자가 말해야 명세가 안 어긋난다 —
    # 갈래 표의 `max_tokens_field` 는 이 계약 하나(openai)만 갈아 끼우는 설정이고,
    # 나머지 둘은 제 계약이 정한 이름(`max_tokens` · `generationConfig.maxOutputTokens`)
    # 을 쓴다. 여기를 안 두면 명세가 표의 이름을 그대로 찍어 **없는 칸을 말한다.**
    cap_field: str


def envelope(system, messages, c):
    """자격 하나로 계약을 갈라 봉투를 짓는다 — **안 보낸다.**

    ⚠ **계약으로 가른다 — 갈래 이름으로 가르지 않는다.** 한 계약을 두 갈래가 쓴다
      (회사 Gemini·내 키 Gemini). 이름으로 가르면 이름이 안 겹치는 갈래가 통째로
      엉뚱한 계약으로 떨어지는데, 화면에는 그냥 실패로만 보인다.
    ⚠ **입력 난간이 여기 선다**(AI-prompt-helper 결정 0024). 봉투를 싸는 자리가 하나라 문마다
      세지 않는다 — 문마다 적으면 반드시 하나가 빠지고, 빠진 문으로 나간 봉투는 게이트웨이가
      조용히 삼킨다.
    """
    build = _ENV_BY_CONTRACT.get(c.contract)
    if build is None:
        raise RuntimeError(f"모르는 계약이다 — {c.contract}")
    layers = _layers(system)
    gauge(layers, messages)
    return build(layers, messages, c)


# ---------- 입력 난간 — 봉투가 벽에 닿기 전에 선다 (결정 0024) ----------

class EnvelopeTooLarge(RuntimeError):
    """봉투가 입력 난간을 넘었다 — **보내기 전에** 선다.

    ⚠ **출력 상한과 다른 축이다.** 저쪽(`gateway.WALL_MAX_TOKENS`)은 우리가 얼마를 받나고
      이쪽은 우리가 얼마를 보내나다. 넘겨 보내면 게이트웨이가 400 을 내거나(그러면
      `_reject_text` 가 말한다) 모르는 것을 삼키는 성질대로 **빈 채로 끊는다** — 뒤엣것이면
      `CUT_NO_SIGNAL` 과 구별이 안 되고, 원인이 입력 쪽이라 되부르기(결정 0023)도 안 듣는다.
    """

    def __init__(self, said, chars, bulk):
        super().__init__(said)
        self.chars = chars      # 봉투가 몇 자였나
        self.bulk = bulk        # 무엇이 컸나 — `[(이름, 자 수), …]` 큰 것부터


def envelope_chars(system, messages):
    """이 봉투가 몇 자인가 — **재기만 한다.** 막는 자는 아래 `gauge` 다.

    부르는 쪽이 난간에 닿기 **전에** 스스로 줄일 수 있게 자를 밖으로 낸다(결정 0024 의
    사슬 접기). 자가 둘이 되지 않게 `gauge` 도 이 함수로 잰다.
    """
    return (sum(len(x) for x in _layers(system))
            + sum(len(_text_of(m["content"])) for m in messages))


def _bulk(layers, messages):
    """무엇이 큰가 — 큰 것부터. **넘을 때만 잰다**: 진단은 자를 때의 말이지 평시 비용이 아니다.

    층은 자리마다 세고 사슬은 한 덩이로 센다 — 사람이 덜어낼 수 있는 단위가 그 둘이라서다
    (층은 문이 고르는 것이고 사슬은 대화 전체다).
    """
    rows = [(f"층 {i + 1}", len(x)) for i, x in enumerate(layers)]
    rows.append((f"대화 {len(messages)}마디",
                 sum(len(_text_of(m["content"])) for m in messages)))
    return sorted(rows, key=lambda row: -row[1])


def gauge(layers, messages):
    """봉투가 난간 안인가 — 넘으면 선다. 돌려주는 것은 잰 자 수다.

    ⚠ **재기만 하고 안 고친다.** 무엇을 접을지는 재료를 아는 쪽(흐름 층)이 안다 — 여기서
      접으면 어댑터가 대화의 뜻을 알아야 하고, 그 순간 이 층이 계약 넷 밖의 것을 진다.
    """
    total = envelope_chars(layers, messages)
    if total <= gateway.MAX_ENVELOPE_CHARS:
        return total
    bulk = _bulk(layers, messages)
    why = " · ".join(f"{name} {n:,}자" for name, n in bulk if n)
    raise EnvelopeTooLarge(
        f"봉투가 입력 난간을 넘었다 — {total:,}자 "
        f"(난간 {gateway.MAX_ENVELOPE_CHARS:,}자). 큰 것부터: {why}",
        total, bulk)


def _layers(system):
    """글자 하나로 와도 **층 목록**으로 맞춘다 — 캐시 경계가 층 위에 서기 때문이다."""
    if isinstance(system, str):
        return [system] if system else []
    return [x for x in (system or []) if x]


def _sealed(env, token):
    """봉투의 빈 키 자리를 채운 머리 — **채우는 자리가 하나여야** 키가 새지 않는다."""
    return {**env.headers, env.key_header: env.key_fmt.format(token)}


def spec(env, c):
    """드라이런이 돌려주는 **명세** — 무엇을 보낼 뻔했나.

    프로브와 서버가 **같은 글**을 본다 — 두 자리에 따로 지으면 한쪽만 낡는다.
    ⚠ 본문은 읽으라고 찍는 것이라 한글을 안 이스케이프한다. 실제로 나가는 바이트는
      `_open` 이 짓고 그쪽은 atelier 가 실측한 꼴 그대로다(아래 곁말).
    """
    body = json.dumps(env.body, ensure_ascii=False, indent=2)
    more = "" if len(body) <= SPEC_BODY_CAP else f"\n…({len(body) - SPEC_BODY_CAP}자 더)"
    heads = ", ".join(k + ("(키 자리 — 비었다)" if k == env.key_header else "")
                      for k in env.headers)
    return "\n".join([
        "[드라이런] 안 보냈다 — 키가 없다",
        f"갈래: {c.provider} · 계약: {c.contract} · 모델: {c.model}",
        f"주소: POST {env.url}",
        f"머리: {heads}",
        f"출력 상한: {env.cap_field}={c.max_tokens}",
        f"캐시 표시: {_cache_slot(env, c)}",
        f"본문: {body[:SPEC_BODY_CAP]}{more}",
    ])


def _cache_slot(env, c):
    """캐시 표시가 어디 섰나 — 계약마다 다르다."""
    if c.contract != gateway.CONTRACT_ANTHROPIC:
        return "이 계약은 접두사가 맞으면 자동이라 실을 표가 없다"
    # 표가 선 자리를 **다** 말한다 — 층이 둘이면 경계도 둘이라(`_ant_system`), 첫 표에서
    # 멈추면 드라이런 명세가 경계 하나만 말하는 거짓말이 된다.
    at = [f"system[{i}].cache_control = " + json.dumps(b["cache_control"], ensure_ascii=False)
          for i, b in enumerate(env.body.get("system") or []) if b.get("cache_control")]
    return " · ".join(at) or "없다 — 고정 층이 안 실렸다"


# ---------- 한 바퀴 · 이어받기 ----------

def stream_once(system, messages, on_text=None, creds=None, on_usage=None,
                deadline=None, on_cut=None, on_think=None):
    """한 바퀴 다녀와서 `(이어붙인 글자, stop_reason)` 을 돌려준다.

    `on_usage` 를 주면 씀씀이를 **Anthropic 어휘로 통일해** 넘긴다 — 갈래마다 이름이
    갈리는 것을 여기서 맞춘다(`_report_usage`). 안 오는 판도 있어 **한 번도 안 불릴
    수 있다.**

    `deadline` 은 길이가 아니라 `time.monotonic()` 의 **시각**이다 — 층을 지나며 다시
    셈할 것이 없어 어긋날 자리가 없다. 소켓 자를 거기서 뽑는다(`_sock_timeout`).

    `on_think` 을 주면 **생각 구간의 누적 추정 토큰**을 넘긴다 — 글자가 아니라 진행이다.
    내는 계약은 둘이다: CLI 갈래(그 계약이 그 줄을 흘린다)와, 생각을 요청하는 gemini 갈래
    (`gateway.GEMINI_THOUGHTS` · 누적치가 `thoughtsTokenCount` 로 온다). 나머지 둘은 한
    번도 안 부른다. **없다고 결함이 아니다** — 안 부르는 계약과 못 받는 계약이 여기서
    갈리지 않고, 가르는 자는 그 계약을 아는 함수다.

    `on_cut` 을 주면 **삼킨 끊김의 사유**를 한 줄로 넘긴다. 스트림이 열린 뒤의 컷은
    예외가 안 오르고 조용히 흡수되므로, 이 자리가 없으면 「끊겼다」만 남고 **무엇에
    끊겼나가 통째로 증발한다** — 게이트웨이가 닫았나 · 리셋인가 · 소켓 시한인가 ·
    우리 예산인가는 성질이 전혀 다른데 기록에는 똑같이 보인다. 그 판의 stop_reason 은
    `None` 이다.

    ⚠ **빈손 둘을 여기서 이름 부른다**(AI-prompt-helper 결정 0023 · 그쪽 #44). 하나는 **빈 채 끊긴 스트림**
      — 접고 한 번 다시 부른다. 다른 하나는 **여문 빈손**(신호가 섰는데 0자) — 되부르지
      않고 사유만 올린다. 계약 넷 공용인 까닭은 「글자가 0 이다」가 계약을 안 가리는
      **상태**라서다(`_empty_why`).

    키가 없으면 **안 보내고** 봉투 명세를 글자로 돌려준다(`STOP_DRY_RUN`).
    """
    c = creds or gateway.creds()
    env = envelope(system, messages, c)
    if c.dry_run:
        # **명세는 계약마다 갈린다**(`_SPEC_BY_CONTRACT`) — CLI 계약은 주소도 머리도
        # 없어 HTTP 명세를 그대로 찍으면 없는 칸을 말한다.
        said = _SPEC_BY_CONTRACT[c.contract](env, c)
        if on_text:
            on_text(said)
        return said, STOP_DRY_RUN
    # 사유는 **스트림 하나에 하나** — 먼저 온 것이 이긴다. 받아 뒀다가 한 번만 올린다.
    why = []
    # 씀씀이를 **여기서도 본다** — 빈손 사유가 그 숫자를 실어야 「생각으로 예산을 다
    # 썼나」를 나중에 물을 수 있다. 흘려보내는 손은 그대로 두고 사본만 든다.
    seen = {}

    def watch(row):
        seen.update(row)
        if on_usage:
            on_usage(row)

    try:
        text, stop = _BY_CONTRACT[c.contract](env, c, on_text, watch,
                                              deadline, why.append, on_think)
    except urllib.error.HTTPError as e:
        # 왜 거부했는지는 응답 몸통에 있다 — 봉투에서 꺼내 사람 말로 싣는다.
        # ⚠ **몸통을 여기서 안 자른다**(결정 0030) — 사람 말 한 줄만 상한을 지고 전문은
        #   예외의 칸으로 간다. 자른 것만 지고 오면 그 뒤로는 전문을 되찾을 자리가 없다.
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = "(응답 몸통 읽기 실패)"
        raise Rejected(_reject_text(e.code, body[:_REJECT_SAY_CAP]), e.code, body) from e
    # **빈 채 끊겼으면 접고 한 번 다시 부른다**(결정 0023) — 받은 것이 없어 잃을 것도
    # 겹칠 것도 없는 그 자리에서만.
    folded = ""
    if _fold_wanted(c, text, stop, deadline):
        folded = CUT_FOLDED
        text, stop = _BY_CONTRACT[c.contract](_plain_env(env), c, on_text, watch,
                                              deadline, why.append, on_think)
    # **끝 신호가 안 섰으면 끊긴 것이다 — 어떻게 끝났든.** 예외로 온 컷은 위에서 이미
    # 사유를 받았고, 조용히 끝난 컷은 여기서 이름을 얻는다(`CUT_NO_SIGNAL` 곁말).
    if stop is None and not why:
        why.append(CUT_NO_SIGNAL)
    # **여문 빈손** — 신호가 섰으므로 위 줄이 안 잡는다. 안 붙이면 사유가 어느 칸에도 안
    # 남고 로그에는 `stop=end_turn out=0` 만 선다(AI-prompt-helper #44 B).
    # ⚠ **안 쟀다** — 이 판정이 계약 전체 위에 선 것은 gemini 에서 난 사고를 일반화한 것이다.
    #   다른 계약이 실제로 여문 빈손을 낸 적이 있나는 양쪽 앱 다 실측이 없다.
    empty = _empty_why(text, stop, seen)
    if empty:
        why.append(empty)
    if folded:
        # 접은 사실이 **앞머리**에 서고 뒤엣것과 한 줄로 잇는다 — `_sse_events.bye` 가
        # 이미 쓰는 자다. 접었는데 또 빈손이면 그 두 사실이 한 줄에 같이 서야 한다.
        why = [f"{folded} · {why[0]}" if why else folded]
    if why and on_cut:
        on_cut(why[0])
    return text, stop


def stream_resumed(system, messages, continue_ask, on_text=None, creds=None,
                   on_usage=None, deadline=None, on_cut=None, on_continue=None,
                   on_seam=None, on_think=None):
    """출력 상한에 걸리면 **이어받아** 끝까지 받는다 — 쪼개기가 아니라 이어붙이기다.

    받은 글을 assistant 마디로 얹고 이어 쓰기 지시를 user 마디로 붙여 다시 부른다.
    봉투의 고정 층은 안 건드리므로 캐시 경계 앞이 바퀴마다 같다.

    ⚠ **지시 문장은 인자로 받고 기본값을 안 둔다.** 지시문의 진본은 앱의 프롬프트 자리라,
      여기 글을 박으면 그 진본이 둘이 된다.
    ⚠ **`max_tokens` 에서만 잇는다.** 신호 없이 끊긴 판(`None`)은 안 잇는다 — 짧고
      닫힌 답에 「계속 내라」를 걸면 이을 것이 없는 채로 **없는 말을 지어낸다.**
      끊김은 `on_cut` 이 사유로 말하고 무엇을 할지는 부르는 쪽이 정한다.
    ⚠ **이음매의 코드 펜스를 벗긴다**(atelier #335 · AI-prompt-helper #45). 지시문으로만 막으면
      안 먹는 판이 있고, 그때 조각은 ```` ```markdown ```` 으로 열려 온다. `parts` 에 앉기
      **전에** 벗기는 까닭은 그 목록이 다음 바퀴의 앞글(assistant 마디)이기 때문이다 —
      뒤에서 벗기면 산출물은 깨끗한데 모델은 펜스 든 앞글을 보고 다음 이음매에서 또 연다.
      벗겼으면 `on_seam` 이 말한다: 조용히 지나가면 「지시문이 먹었다」로 읽힌다.
    ⚠ **`on_seam` 은 이음매마다 부른다 — 벗긴 판만이 아니다.** 셋째 인자가 **그 조각이
      앉은 자리**(이어붙인 글에서의 좌표)이고, 그것이 없으면 위층이 「어디가 이음매였나」를
      영영 모른다. 코드 펜스가 이음매 상처의 전부가 아니라서다: JSON 을 받는 문에서는
      따옴표 한 자만 겹쳐도 판이 통째로 안 열리는데, 그 한 자를 걷으려면 **어디를 볼지**를
      알아야 한다(앱의 이음매 치유 자리). 벗긴 것이 없으면 둘째 인자가 빈 글자다.
    """
    if not (continue_ask or "").strip():
        raise ValueError("이어 쓰기 지시문이 없다 — 진본은 앱의 프롬프트 자리다")
    said, stop = stream_once(system, messages, on_text, creds, on_usage,
                             deadline, on_cut, on_think)
    parts = [said] if said else []
    for i in range(MAX_CONTINUE):
        if stop != "max_tokens":
            break
        if not parts:
            # **이을 것이 없으면 안 잇는다.** 빈 assistant 마디는 계약이 마다하고(400),
            # 「이어 쓴다」는 이을 글이 있을 때의 말이다. 상한에 걸렸다는데 손이 빈 판은
            # 빈손이라, 그 이름은 `stream_once` 가 이미 사유로 올렸다(결정 0023).
            break
        if on_continue:
            on_continue(i + 1)
        convo = list(messages) + [
            {"role": "assistant", "content": "".join(parts)},
            {"role": "user", "content": continue_ask},
        ]
        more, stop = stream_once(system, convo, on_text, creds, on_usage,
                                 deadline, on_cut, on_think)
        more, seam = seam_unfence(more)
        if not more:
            break              # 더 안 나오면 여기가 끝이다 — 같은 앞글로 또 묻지 않는다
        if on_seam:
            # **바퀴 번호는 조각의 것이다** — 첫 부름이 1바퀴라 이 조각은 `i + 2` 다.
            # `on_continue` 가 세는 「몇 번째 이어받기인가」와 하나 어긋나는데, 기록의
            # `lapN` 도막과 눈으로 맞춰야 하는 쪽은 이쪽이다.
            # 좌표는 **벗긴 뒤**의 길이다 — 위층이 보는 글이 그 글이라, 벗기기 전 길이를
            # 주면 가리키는 자리가 벗긴 만큼 밀린다.
            on_seam(i + 2, seam, sum(len(x) for x in parts))
        parts.append(more)
    return "".join(parts), stop


# ---------- 끊김과 거절 ----------

# 스트림이 도중에 끊기면 셋 중 하나로 온다 — FIN(`IncompleteRead`) · RST
# (`ConnectionError`) · 소켓 시한(`TimeoutError`).
_CUT = (http.client.HTTPException, ConnectionError, TimeoutError)
_CUT_WHY_CAP = 200          # 사유가 봉투째 오면 그 한 줄이 도로 기록을 덮는다
# 우리 예산으로 내려놓은 자리 — **저쪽이 끊은 것이 아니다.** 받는 쪽이 이 낱말로 안다.
CUT_BUDGET = "예산이 다했다"
# 못 읽고 버린 조각 — 잃었다는 **사실**이라 예외 사유와 갈리는 낱말로 온다.
# 몸통은 안 싣는다: 조각은 본문일 수 있고 이 통로는 기록 한 줄이다.
CUT_LOST = "안 여민 봉투 조각 {n}자를 버렸다"
# **예외 없이 조용히 끝난 컷** — 저쪽이 스트림을 규격대로 닫아 놓고 끝 프레임을 안 준
# 판이다. ENV-posco 64–68행의 그 사태(`message_start` 하나만 받고 180초 뒤 끊김)가 이
# 꼴로 온다. 예외가 안 나므로 사건으로 재면 **영영 안 걸린다** — 그래서 판정을
# 「예외가 났나」가 아니라 **「종료 신호가 섰나」** 위에 세운다(`stream_once` 끝).
# ⚠ 실측(이 저장소 · 파이썬 3.14): 잘린 Content-Length 응답도, 깨끗이 닫힌 청크
#   스트림도 `readline()` 이 조용히 끝난다 — 예외로 오는 것은 **잘린 청크**뿐이다.
CUT_NO_SIGNAL = "종료 신호 없이 스트림이 끝났다"
_WALL_FLOOR_S = 1.0         # 예산이 바닥나도 **한 번은** 다녀올 기회를 준다

# **여문 빈손** — 저쪽이 「다 말했다」고 신호를 세워 놓고 글자를 한 자도 안 준 판이다.
# 끊긴 것이 아니라 여문 것이라 이름이 따로 서야 한다: 위 `CUT_NO_SIGNAL` 은 **신호가
# 없는** 자리를 잡고, 이쪽은 **신호가 선** 자리를 잡는다. 이름이 하나면 뒤엣것이 영영
# 안 걸린다 — 로그에 `stop=end_turn out=0` 만 서고 사유 칸은 빈다(AI-prompt-helper #44 B).
EMPTY_HANDS = "여문 빈손 — 종료 신호가 섰는데 글자가 0 이다"
# 접은 길 — 빈 채 끊긴 스트림을 **스트리밍만 접고** 한 번 다시 부른 판(AI-prompt-helper 결정 0023).
CUT_FOLDED = "빈 채 끊겨 접고 한 번 다시 불렀다"
# 안 온 씀씀이 칸의 표. **0 과 갈려야 한다** — 「저쪽이 0 을 실었다」와 「아예 안 실었다」는
# 다른 진단이고, 빈손을 캘 때 갈리는 것이 바로 그 둘이다. `log.MISSING` 이 표 칸에서 드는
# 같은 규율이고 여기 것은 **문장에 실리는 말**이라 글자가 다르다.
_NO_CELL = "칸 없음"
# 빈손 사유에 싣는 씀씀이 — 「생각으로 예산을 다 썼나」를 그 자리에서 묻는 칸들이다.
# ⚠ **`output_reported` 가 곁에 선다** — 「0 을 실었다」와 「칸을 아예 안 실었다」가
#   빈손 진단에서 갈리는 두 사실이고, 앞엣것만 보면 게이트웨이가 안 센 판이 모델이 한
#   자도 안 뱉은 판으로 읽힌다(아뜰리에 #302 ③).
# ⚠ **`thinking_tokens` 는 든 계약에만 있다** — 없으면 `_NO_CELL` 로 서고, 그것이 곧
#   「이 갈래는 그 칸을 안 준다」는 참말이다.
_EMPTY_CELLS = ("output_tokens", "output_reported", "thinking_tokens", "total_input")


def _empty_why(text, stop, usage):
    """여문 빈손인가 — 맞으면 **사유 한 줄**, 아니면 빈 글자.

    ⚠ **판정은 상태 위에 선다** — 이 부름이 돌려준 것 셋(글자 · 종료 신호 · 씀씀이)이
      전부다. 「어느 계약이냐」를 안 묻는 까닭은 0자가 계약을 안 가리는 상태라서다:
      갈래마다 넷을 고치면 새 계약을 다는 사람이 그중 하나를 빠뜨린다.
    ⚠ **드라이런은 빈손이 아니다** — 안 보낸 호출이라 저쪽이 준 것이 애초에 없다.
    ⚠ **「없음」을 0 으로 안 접는다**(위 `_NO_CELL`).
    """
    if (text or "").strip() or stop is None or stop == STOP_DRY_RUN:
        return ""
    seat = usage or {}
    said = " · ".join(f"{k}={seat[k] if k in seat else _NO_CELL}"
                      for k in _EMPTY_CELLS)
    return f"{EMPTY_HANDS} · stop={stop} · {said}"


def _plain_env(env):
    """**스트리밍만 접은 같은 봉투** — 주소도 본문도 그대로고 두 칸만 갈린다.

    읽개를 새로 안 짓는 까닭은 `_anthropic_once` 의 `text/event-stream` 이 아닌 갈래가
    이미 통짜 몸통을 읽기 때문이다. 봉투를 다시 짓지 않고 `_replace` 로 두 칸만 가는
    까닭도 같다 — 다시 지으면 층·경계·상한이 저쪽과 갈릴 자리가 생긴다.
    """
    return env._replace(headers={**env.headers, "accept": "application/json"},
                        body={**env.body, "stream": False})


def _fold_wanted(c, text, stop, deadline):
    """빈 채 끊긴 스트림인가 — 접고 다시 부를 자리인가 (결정 0023).

    ⚠ **조건을 좁게 둔다.** 조각이 한 자라도 흘렀으면 안 부른다 — 그 판은 이어받기의
      자리이고, 여기서 다시 부르면 같은 글을 두 번 생성해 값만 두 배가 된다.
    ⚠ **예산이 남았을 때만** — 시간에 걸려 온 판에 한 바퀴를 더 얹지 않는다.
    ⚠ **anthropic 계약만** — 접은 길을 실측한 자리가 거기 하나다(atelier 0202 · 4.80초).
      나머지 셋은 **안 쟀다**: gemini 는 접으면 끝점 이름부터 갈리고(`:generateContent`),
      CLI 는 접을 스트림이 없다. 그 갈래들도 빈손이면 위 `_empty_why`·`CUT_NO_SIGNAL` 이
      이름은 부르므로 **조용히 지나가지는 않는다.**
    ⚠ **한 이벤트도 못 받은 판은 여기 안 온다** — `_sse_events` 가 그때는 안 삼키고
      예외로 올린다(`if not got: raise`).
    """
    return (c.contract == gateway.CONTRACT_ANTHROPIC
            and stop is None and not (text or "").strip()
            and (deadline is None or time.monotonic() < deadline))


# ---------- 이어쓰기 이음매의 코드 펜스 ----------
# atelier app/providers.py `seam_unfence`·`_join_seams` 에서 가져왔다 (아뜰리에 #335 ·
# 2026-09-05 실물). **손으로 따라간다** — 저쪽이 고치면 여기도 고친다(저쪽 그 절에도 적혀 있다).
#
# 이음매는 **두 자리**에 선다 — 우리 봉합(`stream_resumed` · HTTP 계약 셋)과 **CLI 갈래 안**
# (`_cli_once` · 앞 메시지가 출력 상한에서 잘리면 CLI 가 스스로 둘째 메시지로 잇는다).
# 벗기는 자는 한 벌이고 둘이 같이 쓴다 — 한 자리만 벗기면 다른 자리의 펜스가 산출물
# 한복판에 앉는다. 문서에서는 흠이고 코드에서는 치명이다: 이음매가 스크립트 한가운데면
# 그 한 줄이 문법 오류라 앱이 통째로 죽는다.
#
# ⚠ **머리가 증거고 꼬리는 그 짝이다.** 머리 펜스 없이 온 꼬리 펜스는 안 건드린다 —
#   한쪽만 보고 벗기면 본문 안의 코드 블록 한 장을 반쪽 낸다.
# ⚠ **앱이 최종본에 거는 벗기기와 다른 자다.** 저쪽은 `\A…\Z` 앵커라 **최종본의 앞뒤 한 겹**만
#   벗긴다 — 이음매는 글 한복판이라 그 자에 안 걸린다.
_SEAM_FENCE_HEAD = re.compile(r"\A[ \t]*```[a-zA-Z]*[ \t]*\r?\n")
_SEAM_FENCE_TAIL = re.compile(r"\r?\n[ \t]*```[ \t]*\s*\Z")


def seam_unfence(more):
    """이어쓰기 조각에서 이음매 펜스를 벗긴다 — `(조각, 벗긴 것 | "")`."""
    head = _SEAM_FENCE_HEAD.match(more or "")
    if not head:
        return more, ""
    more = more[head.end():]
    tail = _SEAM_FENCE_TAIL.search(more)
    if tail:
        return more[:tail.start()], "머리+꼬리"
    return more, "머리"


def _join_seams(out, seams):
    """CLI 자식이 낸 메시지 여러 개를 한 글로 — 둘째부터는 이음매 펜스를 벗긴다.

    `seams` 는 둘째 메시지부터가 `out` 의 어디서 시작하나다(`_cli_once` 가 `message_start`
    마다 적는다). 비면 종전과 바이트로 같다.
    ⚠ 저쪽은 벗긴 자리를 콘솔에 찍는데 여기는 안 찍는다 — 이 층은 콘솔에 아무것도 안 찍는
      규율이라(기록은 `log` 가 든다) 벗김은 조용하다. 몇 번 벗겼나를 남길 자리가 필요해지면
      `on_cut` 처럼 부르는 쪽이 받는 자를 세운다.
    """
    if not seams:
        return "".join(out)
    text, prev = "", 0
    for at in seams + [len(out)]:
        seg = "".join(out[prev:at])
        if prev:
            seg, _why = seam_unfence(seg)
        text += seg
        prev = at
    return text


def _why(exc):
    """예외 하나를 한 줄 사유로 — 이름과 뜻을 붙여 자른다."""
    return f"{type(exc).__name__}: {exc}".splitlines()[0][:_CUT_WHY_CAP]


def _sock_timeout(deadline):
    """소켓에 걸 자 — 침묵 시계와 남은 예산 중 **먼저 오는 쪽.**

    `gateway.TIMEOUT_S` 는 총 시간이 아니라 **침묵**을 재므로 조각이 흐르는 동안 영영
    안 운다. 예산을 받으면 그보다 길게 눕지 않게 깎는다.
    """
    if deadline is None:
        return gateway.TIMEOUT_S
    return max(_WALL_FLOOR_S, min(gateway.TIMEOUT_S, deadline - time.monotonic()))


def _one_line(text):
    """여러 줄·태그로 온 몸통을 한 줄 말로 접는다 — 낱말은 안 버린다.

    앞단이 HTML 로 거부를 보내면(504) 마크업이 통째로 오류 글에 실린다. 태그는 `<` 로
    시작하는 몸통에서만 걷는다 — 아무 데나 걸면 산문 속 부등호가 낱말째 사라진다.
    """
    t = (text or "").strip()
    if t.startswith("<"):
        t = re.sub(r"<[^>]{0,200}>", " ", t)
    return " ".join(t.split())


class Rejected(RuntimeError):
    """게이트웨이가 HTTP 로 거절했다 — **몸통을 자른 데 없이 지고 온다**(AI-prompt-helper 결정 0030).

    사람 말 한 줄은 예외 글자가 들고(그 글자가 화면과 기록에 같이 선다), **전문은 칸으로**
    따로 든다. 두 자리의 상한이 다르기 때문이다 — 화면 줄도 기록 줄도 한 줄 계약이라 자르는데,
    게이트웨이가 봉투째 실어 보낸 거절 본문은 그 길이를 예사로 넘는다. 자른 뒤에는 「그 404 가
    어디서 왔나」를 되물을 재료가 아무 데도 안 남는다. 형제 하나는 2,000자에서 잘라 문자열에
    섞는데 그쪽에 기록층이 없어서였지 판단이 아니다 — 구조로 지니는 것이 상위다.

    ⚠ **전문을 예외 글자에 안 싣는다** — 실으면 화면과 기록이 그 한 줄에 덮인다. 굳히는
      자는 앱의 흐름 층이고 앉는 자리는 그 판 곁이다.
    """

    def __init__(self, said, status, body):
        super().__init__(said)
        self.status = status    # HTTP 상태 줄
        self.body = body        # 응답 몸통 **전문** — 자른 데가 없다


# 거절 한 줄에 실을 몸통의 상한 — **전문은 위 `Rejected.body` 가 든다.**
_REJECT_SAY_CAP = 2000


def _reject_text(status, body):
    """HTTP 거부 몸통 → 사람이 읽는 한 줄.

    봉투 꼴은 넷이고 진본은 `claude-config/posco/errors-Posco.setting.md` 다 — 「포맷
    wrap, 코드 패스스루」. 여기서는 두 꼴만 편다: `{"error":{...}}`(Native·Messages)와
    평평한 `{"code","message"}`(Legacy).
    ⚠ **코드 표를 옮겨 적지 않는다** — 뜻은 저 문서가 든다. 메시지는 게이트웨이의
      한국어 그대로 싣고 코드는 실려 오면 붙인다(카탈로그를 찾는 열쇠라서).
    ⚠ **Messages API 응답에는 P-GPT 코드가 안 실린다**(같은 문서 240행) — 코드 칸이
      비는 것이 결함이 아니다.
    """
    try:
        data = json.loads(body)
    except ValueError:
        data = None
    seat = data if isinstance(data, dict) else {}
    if isinstance(seat.get("error"), dict):
        seat = seat["error"]
    msg, code = seat.get("message"), seat.get("code")
    if not isinstance(msg, str) or not msg.strip():
        return f"게이트웨이 HTTP {status}: {_one_line(body)}"
    return f"게이트웨이 HTTP {status} — {_one_line(msg)}" + (f" ({code})" if code else "")


def _sse_events(resp, deadline=None, on_cut=None):
    """SSE 응답에서 JSON 이벤트를 하나씩 꺼내 준다 — 계약 셋이 같이 쓴다.

    ⚠ **끊김을 여기서 삼킨다.** 스트림이 시작된 뒤의 시간 초과는 깨끗한 HTTP 오류로
      올 수가 없다 — 머리가 이미 200 으로 나갔으니 상태를 되돌릴 방법이 없어 저쪽은
      TCP 를 닫는다. 받은 조각은 호출자 손에 남고 stop 이 빈 채로 돌아간다.
      사내의 180초 벽(`gateway.GATEWAY_WALL_S`)이 이 자리로 온다.
    ⚠ **하나도 못 받고 끊겼으면 안 삼킨다** — 이어붙일 것이 없는 진짜 오류라 예외로
      올려야 화면에 보인다.
    ⚠ **삼키더라도 사유는 올린다**(`on_cut`) — 안 그러면 그 자리에서 사유가 증발한다.
    ⚠ **쪼개진 봉투를 여민다.** 이 게이트웨이는 긴 몸통을 여러 `data:` 줄로 갈라
      보낸다(atelier #118 회사 실측). 줄마다 파싱하면 못 읽은 조각이 **조용히**
      버려진다 — 버리게 되면 그 사실과 크기를 사유로 올린다(`CUT_LOST`).
    """
    got = False
    pend = ""                 # 쪼개진 봉투의 앞 조각 — 여며질 때까지 든다
    lost = 0                  # 못 읽고 버린 글자 수
    evname = ""               # 직전 `event:` 줄 — 사내 `event:error` 프레임용

    def bye(why=""):
        n = lost + len(pend)
        if n:
            why = (why + " · " if why else "") + CUT_LOST.format(n=n)
        if why and on_cut:
            on_cut(why)

    try:
        for raw in resp:
            if deadline is not None and time.monotonic() >= deadline:
                # 예산이 다했다 — 컷과 똑같이 내려놓는다. 새 갈래를 안 만드는 것이 요점.
                bye(CUT_BUDGET)
                return
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.lstrip().startswith("event:"):
                evname = line.lstrip()[6:].strip()
                continue
            if not line.lstrip().startswith("data:"):
                continue
            payload = line.lstrip()[5:]
            if payload.startswith(" "):
                payload = payload[1:]
            if payload.strip() == "[DONE]":
                bye()          # 저쪽이 끝을 말했어도 꼬리가 남으면 잃은 것이다
                return
            buf = pend + payload
            try:
                ev = json.loads(buf)
            except ValueError:
                # 깨진 꼬리가 뒤 봉투까지 삼키지 않게, 홀로 서는 새 봉투가 오면
                # 꼬리를 버리고 그것부터 잇는다 — 버린 몫은 세어 둔다.
                if pend and payload.lstrip().startswith("{"):
                    try:
                        ev = json.loads(payload)
                    except ValueError:
                        pend = buf
                        continue
                    lost += len(pend)
                    pend = ""
                    got = True
                    yield ev
                    continue
                pend = buf
                continue
            pend = ""
            if evname == "error":
                # 사내 문서 「SSE error event」 — 스트림이 200 으로 이미 열려 있어
                # 오류가 프레임으로 온다. 안 받으면 조용히 빈 응답으로만 보인다.
                raise RuntimeError("게이트웨이 스트림 오류 — "
                                   + (ev.get("message") or "사유 없음")
                                   + (f" ({ev['code']})" if ev.get("code") else ""))
            evname = ""
            got = True
            yield ev
        bye()
    except _CUT as exc:
        if not got:
            raise
        bye(_why(exc))


# ---------- 씀씀이 — 계약마다 다른 이름을 한 어휘로 ----------

def _report_usage(on_usage, usage, prompt_key="input_tokens",
                  read_key="cache_read_input_tokens",
                  write_key="cache_creation_input_tokens",
                  out_key="output_tokens", cache_is_extra=True,
                  think_key=""):
    """턴마다 토큰 씀씀이를 **Anthropic 어휘로 통일해** 넘긴다.

    ⚠ **총 입력은 계약마다 다르게 센다** — `cache_is_extra` 가 그 갈림이다. Anthropic 은
      `input_tokens` 에서 캐시분을 **빼고** 보고해서 셋을 더해야 봉투 크기가 된다
      (atelier 실측 2026-08-18: `in=2 · read=5,003 · write=45,310`). OpenAI·Gemini 는
      프롬프트 총량 하나로 보고하고 캐시 항목은 그 **부분집합**이라 더하면 두 번 센다.
    ⚠ **0 판정은 `input_tokens` 이 아니라 합으로 한다.** 캐시가 통째로 걸리면
      `input_tokens` 가 0 이 되는데 그것으로 거르면 **가장 잘 걸린 판이 기록에서
      빠진다.** 거르려는 것은 게이트웨이가 아직 안 세고 보낸 **빈 보고**다 —
      그 판은 캐시 칸도 0 이라 합이 0 이고, 그래서 합으로 재면 둘이 갈린다.
    """
    if not usage or not on_usage:
        return
    n = int(usage.get(prompt_key) or 0)
    read, write = int(usage.get(read_key) or 0), int(usage.get(write_key) or 0)
    out = int(usage.get(out_key) or 0)
    total = n + read + write if cache_is_extra else n
    # 생각에 쓴 몫 — **든 계약만 싣는다**(`think_key`). 없는 계약은 칸이 아예 안 선다.
    think = usage.get(think_key) if think_key else None
    if not total:
        return
    seat = {"input_tokens": n, "cache_read": read, "cache_write": write,
            # 봉투가 실제로 몇 토큰이었나 — **읽는 쪽은 이것만 보면 된다.**
            "total_input": total,
            # 이 바퀴가 뱉은 몫 — 이어받기가 걸리면 다음 바퀴 입력에 되실린다.
            "output_tokens": out,
            # ⚠ **「0 이었다」와 「칸이 안 왔다」는 다른 일이다**(아뜰리에 #302 ③). 위
            #   `or 0` 이 둘을 같은 숫자로 접는데, 빈손을 진단할 때 갈리는 것이 바로 그
            #   둘이다 — **모델이 정말 한 자도 안 뱉었나**와 **게이트웨이가 안 세고
            #   보냈나**. 숫자 옆에 「보내긴 했나」를 세워 갈라 둔다.
            # ⚠ 없을 때만 서는 칸이 아니라 **늘 서는 참거짓**이다: 씀씀이는 바퀴마다
            #   덮어써 합쳐지므로, 없을 때만 세우면 먼저 온 벌의 「안 왔다」가 뒤엣것에
            #   안 지워진 채 남는다.
            "output_reported": out_key in usage}
    if isinstance(think, int):
        # 생각 토큰이 바퀴 기록까지 내려온다 — 「생각으로 예산을 다 썼나」를 긍정도
        # 부정도 못 하던 자리다(아뜰리에 #302 ③). `on_think` 는 화면 진행 신호라 흘러가
        # 사라지고, **기록에 남는 자리는 여기 하나**다.
        seat["thinking_tokens"] = think
    on_usage(seat)


# ---------- 보내는 자리 ----------

def _open(env, c, deadline):
    """봉투를 실제로 올린다 — **키가 봉투에 들어가는 유일한 자리**다.

    ⚠ 몸통은 한글을 이스케이프해 보낸다(`json.dumps` 기본값) — atelier 가 이 게이트웨이로
      실측한 꼴 그대로다. 읽으라고 찍는 명세만 안 이스케이프한다(`spec`).
    """
    req = urllib.request.Request(
        env.url, data=json.dumps(env.body).encode("utf-8"), method="POST",
        headers=_sealed(env, c.token))
    return urllib.request.urlopen(req, timeout=_sock_timeout(deadline))


def _is_sse(resp):
    return "text/event-stream" in (resp.headers.get("content-type") or "")


# ---------- Anthropic 계약 ----------

# 한 요청에 설 수 있는 캐시 경계의 수 — **계약이 정한 상한이다.** 넘기면 요청이 통째로
# 거절된다 — 캐시가 안 걸리는 것이 아니라 그 부름이 죽는다(atelier 결정 0100 이 실측하고
# 그 자리에서 물린 값이다).
# ⚠ **넷을 누가 쓰나는 앱의 정책이다.** system 층 사이에만 두는 앱(헬퍼)과 system 과 대화
#   마디가 나눠 쓰는 앱(아뜰리에 결정 0109)이 다 맞다 — 그래서 `_ant_system` 이 예산을
#   인자로 받는다. 마디에도 경계를 두는 앱은 그만큼 뺀 예산을 준다.
CACHE_MARK_CAP = 4
# system 층이 쓸 경계 예산 — 마디에도 경계를 두는 앱은 복사한 뒤 여기서 그만큼 뺀다.
SYSTEM_MARKS_BUDGET = CACHE_MARK_CAP


def _cache_ctl():
    """캐시 표시 한 덩이 — 수명이 기본(5분)이 아니면 그 값을 함께 싣는다."""
    ctl = {"type": "ephemeral"}
    if gateway.CACHE_TTL and gateway.CACHE_TTL != "5m":
        ctl["ttl"] = gateway.CACHE_TTL
    return ctl


def _ant_system(layers, marks_budget=CACHE_MARK_CAP):
    """층 목록 → system 덩이들. **캐시 경계는 층과 층 사이마다 선다.**

    표시는 「여기까지의 앞부분을 캐시하라」는 뜻이다. 층을 `[고정 층…, 턴 지시문]` 순으로
    쌓으면 경계가 갈 자리는 **고정 층 끝마다**고 맨 뒤 턴 지시문 끝에는 안 간다 — 「공통 층
    → 경계 → 턴 지시문 → 가변부」의 순서다(AI-prompt-helper 결정 0004). 층이 둘이면 경계
    하나, 셋이면 둘이다.

    `marks_budget` — 이 system 이 쓸 수 있는 경계 수. 계약 상한은 넷(`CACHE_MARK_CAP`)이고
    대화 마디에도 경계를 두는 앱은 그만큼 뺀 값을 준다 — 예산을 안 나누면 마디 쪽 경계와
    합쳐 넷을 넘겨 요청이 통째로 거절된다.

    ⚠ **첫 층에만 붙이면 둘째 고정 층이 조용히 캐시 밖으로 나간다**(AI-prompt-helper 결정
      0014). 표시가 없어도 요청은 멀쩡히 나가고 화면도 그대로라, 안 걸린 것은 **씀씀이
      기록에서만** 보인다.
    ⚠ **층이 하나면 그 하나에 붙인다.** 위 규칙대로면 경계가 0 이 되는데, 어차피 짧아 계약
      최소 길이에 못 미치는 판이라 붙든 안 붙든 값이 같고 **안 바꾸는 쪽**을 고른다.
    ⚠ **실측 2026-09-09** — 층 셋(각 4,000자)에 표를 둘 달아 두 번 보냈더니 첫 판이 8,005토큰을
      쓰고 둘째 판이 **8,005 을 그대로 읽었다**(`_check/live_probe.py cache-layers` · claude-opus-5).
      표가 선 두 층이 다 캐시에 든다 — 표를 안 다는 쪽이 캐시 밖이지, 표를 달았는데 둘째 층만
      빠지는 일은 없다.

    무엇을 층에 싣나는 여기 몫이 아니다 — 앱이 정한다.
    """
    marks = min(max(len(layers) - 1, 1), marks_budget)
    return [{"type": "text", "text": text,
             **({"cache_control": _cache_ctl()} if i < marks else {})}
            for i, text in enumerate(layers)]


def _ant_envelope(layers, messages, c):
    heads = {"content-type": "application/json",
             "anthropic-version": gateway.ANTHROPIC_VERSION,
             "accept": "text/event-stream"}
    if c.betas:
        # 갈래마다 싣는 낱말이 다르다 — 왜는 갈래 표의 `betas` 칸이 든다.
        heads["anthropic-beta"] = ",".join(c.betas)
    heads["x-api-key"] = ""
    return Envelope(
        url=c.url,
        headers=heads,
        body={"model": c.model,
              "max_tokens": c.max_tokens,
              "stream": True,
              # 층이 없으면 키 자체를 안 싣는다 — 빈 배열은 계약이 마다한다.
              **({"system": _ant_system(layers, SYSTEM_MARKS_BUDGET)} if layers else {}),
              "messages": [{"role": m["role"], "content": m["content"]}
                           for m in messages]},
        key_header="x-api-key",
        key_fmt="{}",
        cap_field="max_tokens")


def _anthropic_once(env, c, on_text, on_usage, deadline, on_cut, on_think=None):
    with _open(env, c, deadline) as resp:
        if not _is_sse(resp):
            # 스트림을 안 열어도 배관이 죽지 않게 통짜 응답을 그대로 받는다.
            data = json.loads(resp.read().decode("utf-8"))
            _report_usage(on_usage, data.get("usage"))
            text = "".join(b.get("text", "") for b in data.get("content") or [])
            if text and on_text:
                on_text(text)
            return text, data.get("stop_reason")

        parts, stop = [], None
        for ev in _sse_events(resp, deadline, on_cut):
            kind = ev.get("type")
            if kind == "message_start":
                _report_usage(on_usage, (ev.get("message") or {}).get("usage"))
            elif kind == "content_block_delta":
                piece = (ev.get("delta") or {}).get("text", "")
                if piece:
                    parts.append(piece)
                    if on_text:
                        on_text(piece)
            elif kind == "message_delta":
                stop = (ev.get("delta") or {}).get("stop_reason") or stop
                # 여기서도 본다 — 사내 게이트웨이는 진짜 입력 토큰을 이 이벤트에
                # 싣는다(`message_start` 는 0 이었다 · atelier 실측).
                _report_usage(on_usage, ev.get("usage"))
            elif kind == "error":
                raise RuntimeError((ev.get("error") or {}).get(
                    "message", "게이트웨이 오류"))
    return "".join(parts), stop


# ---------- OpenAI 계약 — /v1/responses ----------

def _oa_envelope(layers, messages, c):
    return Envelope(
        url=c.url,
        headers={"content-type": "application/json",
                 "accept": "text/event-stream",
                 "authorization": ""},
        body={"model": c.model,
              # 상한을 실을 이름은 갈래 표가 든다 — 이 계약만 `max_output_tokens` 다.
              c.max_tokens_field: c.max_tokens,
              "stream": True,
              # 저쪽에 대화를 안 남긴다 — 사슬은 우리가 든다.
              # ⚠ 이 낱말은 사내 문서 파라미터 표 밖이다(「추가 파라미터는 그대로
              #   전달」 · OpenAI.-Posco.Setting.md 참고 사항). **안 쟀다.**
              "store": False,
              # system 층이 제 칸을 얻는다 — 첫 메시지로 접을 필요가 없다.
              **({"instructions": "\n\n".join(layers)} if layers else {}),
              "input": [{"role": m["role"], "content": _text_of(m["content"])}
                        for m in messages]},
        key_header="authorization",
        key_fmt="Bearer {}",
        cap_field=c.max_tokens_field)


def _openai_once(env, c, on_text, on_usage, deadline, on_cut, on_think=None):
    with _open(env, c, deadline) as resp:
        if not _is_sse(resp):
            data = json.loads(resp.read().decode("utf-8"))
            _oa_usage(on_usage, data.get("usage"))
            text = "".join(
                part.get("text", "")
                for it in data.get("output") or [] if it.get("type") == "message"
                for part in it.get("content") or []
                if part.get("type") == "output_text")
            if text and on_text:
                on_text(text)
            return text, _oa_stop(data)

        parts, final = [], None
        for ev in _sse_events(resp, deadline, on_cut):
            kind = ev.get("type")
            if kind == "response.output_text.delta":
                piece = ev.get("delta") or ""
                if piece:
                    parts.append(piece)
                    if on_text:
                        on_text(piece)
            elif kind in ("response.completed", "response.incomplete"):
                final = ev.get("response") or {}
                # 씀씀이는 완성본에만 실린다 — 컷이 나면 그 바퀴 값은 아예 없다.
                _oa_usage(on_usage, final.get("usage"))
            elif kind == "response.failed":
                raise RuntimeError(((ev.get("response") or {}).get("error") or {})
                                   .get("message", "게이트웨이 오류"))
            elif kind == "error":
                raise RuntimeError(ev.get("message") or "게이트웨이 오류")
    return "".join(parts), _oa_stop(final)


def _oa_stop(final):
    """Responses 종료 → Anthropic 어휘.

    옛 문의 `finish_reason` 낱말이 여기서는 **응답 상태**다. 완성본이 아예 안 왔으면
    (컷) None — 그 빈 자리는 `on_cut` 이 사유로 말한다. 잘림은 `incomplete` +
    `incomplete_details.reason` 으로 온다. 모르는 까닭은 **그대로 올린다** — 거절에
    이어받기를 걸면 같은 거절을 바퀴 수만큼 다시 받는다.
    """
    if not final:
        return None
    status = final.get("status")
    if status == "completed":
        return "end_turn"
    if status == "incomplete":
        why = (final.get("incomplete_details") or {}).get("reason")
        return "max_tokens" if why == "max_output_tokens" else why
    return status


def _oa_usage(on_usage, usage):
    """Responses 씀씀이 — 이름만 갈아 끼워 공용 자리로.

    걸린 캐시가 한 겹 안에 실려 와서(`input_tokens_details.cached_tokens`) **읽을 때
    한 번 편다** — 안 펴면 「캐시가 걸렸나」를 영영 못 본다. 쓰기 칸은 표준에 없는데
    이 게이트웨이가 곁에 얹어 준다(atelier #123 실측 · 비표준) — 안 오는 판은 0 이다.
    `input_tokens` 가 **이미 총량**이라 더할 것이 없다.
    """
    if not usage:
        return
    flat = dict(usage)
    inner = flat.get("input_tokens_details") or {}
    flat["cached_tokens"] = inner.get("cached_tokens") or 0
    flat["cache_write_tokens"] = inner.get("cache_write_tokens") or 0
    _report_usage(on_usage, flat, prompt_key="input_tokens",
                  read_key="cached_tokens", write_key="cache_write_tokens",
                  out_key="output_tokens", cache_is_extra=False)


# ---------- Gemini 계약 — 구글 네이티브 ----------

def _gm_envelope(layers, messages, c):
    """`url` 이 **바닥 주소**다 — 이 계약만 경로에 모델 이름이 들어간다."""
    return Envelope(
        url=(f"{c.url.rstrip('/')}/v1beta/models/{c.model}"
             f":streamGenerateContent?alt=sse"),
        headers={"content-type": "application/json",
                 "accept": "text/event-stream",
                 "x-goog-api-key": ""},
        body={
            # system 이 messages 밖에 따로 선다 — Anthropic 과 같은 자리다.
            **({"systemInstruction": {"parts": [{"text": t} for t in layers]}}
               if layers else {}),
            # 역할 이름이 다르다 — assistant 가 여기서는 `model` 이다.
            "contents": [{"role": "model" if m["role"] == "assistant" else "user",
                          "parts": [{"text": _text_of(m["content"])}]}
                         for m in messages],
            # 생각을 **요청한다** — 그 조각이 흘러 앞단의 무응답 자가 계속 되돌아간다
            # (`gateway.GEMINI_THOUGHTS` 곁말 · 아뜰리에 실측 2026-08-27).
            # ⚠ 생각 조각은 본문이 아니다 — 거르는 자는 아래 `_gemini_take` 다. **난간이
            #   손잡이보다 먼저 서 있었다**: 그 자리는 안 켜던 날에도 있었다.
            "generationConfig": {
                # 생각 몫이 이 상한 안에 든다 — 답 크기(`c.max_tokens`)에 그 몫을 더하되 모델
                # 상한은 못 넘긴다(`gateway.GEMINI_THINK_TOKENS` 곁말).
                "maxOutputTokens": min(c.max_tokens + gateway.GEMINI_THINK_TOKENS,
                                       gateway.model_cap(c.model)),
                **({"thinkingConfig": {"includeThoughts": True}}
                   if gateway.GEMINI_THOUGHTS else {}),
            },
        },
        key_header="x-goog-api-key",
        key_fmt="{}",
        cap_field="generationConfig.maxOutputTokens")


def _gemini_once(env, c, on_text, on_usage, deadline, on_cut, on_think=None):
    with _open(env, c, deadline) as resp:
        if not _is_sse(resp):
            data = json.loads(resp.read().decode("utf-8"))
            _gm_usage(on_usage, data.get("usageMetadata"), on_think)
            text, stop = _gemini_take(data, None)
            if text and on_text:
                on_text(text)
            return text, stop

        parts, stop = [], None
        for ev in _sse_events(resp, deadline, on_cut):
            if ev.get("error"):
                raise RuntimeError(ev["error"].get("message", "게이트웨이 오류"))
            # **이 계약만 씀씀이를 조각마다 싣는다** — 캐시 칸은 마지막 덩이에만 온다.
            _gm_usage(on_usage, ev.get("usageMetadata"), on_think)
            piece, stop = _gemini_take(ev, stop)
            if piece:
                parts.append(piece)
                if on_text:
                    on_text(piece)
    return "".join(parts), stop


def _gemini_take(ev, stop):
    """한 덩이에서 (글자, stop_reason) 을 꺼낸다 — 스트림·통짜 공용.

    ⚠ **생각 part 는 본문이 아니다.** 생각을 요청하면(`gateway.GEMINI_THOUGHTS`) 같은
      `parts` 배열에 `thought: true` 를 달고 **섞여** 온다 — 따로 오지 않는다. 안 거르면
      모델의 속말이 산출물 한복판에 앉는다.
      켜고 끄는 것과 무관하게 늘 거른다: 꺼져 있으면 올 것이 없어 무해하다.
      **난간은 손잡이보다 먼저 서 있어야 한다.**
    """
    cand = (ev.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "")
                   for p in ((cand.get("content") or {}).get("parts") or [])
                   if not p.get("thought"))
    return text, _map_gemini_finish(cand.get("finishReason")) or stop


def _map_gemini_finish(fin):
    """`finishReason` 을 Anthropic 어휘로 — 이어받기가 그대로 걸리게."""
    if fin == "MAX_TOKENS":
        return "max_tokens"
    if fin == "STOP":
        return "end_turn"
    return fin


def _gm_usage(on_usage, meta, on_think=None):
    """Gemini 씀씀이 — 이름만 갈아 끼워 공용 자리로.

    `promptTokenCount` 가 **이미 총량**이고 캐시분(`cachedContentTokenCount`)은 그 안에
    든 부분집합이라 더하지 않는다. 쓰기 칸은 이 계약에 없다 — 캐시가 자동이라 우리가
    실을 표도, 저쪽이 「썼다」고 셀 칸도 없다.

    ⚠ **생각 몫도 씀씀이 칸으로 내려보낸다**(아뜰리에 #302 ③) — 아래 `on_think` 는 화면
      진행 신호라 흘러가 사라지고, 뒤에 「생각으로 예산을 다 썼나」를 물으면 답할 재료가
      아무 데도 안 남는다. 이름 갈아 끼우는 자리가 여기 하나다.
    ⚠ **사내 문서의 `usageMetadata` 목록에 이 칸이 없다.** 목록 밖인데 오는 칸이 이미
      있으므로(`cachedContentTokenCount`) **있으면 쓰고 없으면 조용하다** — 지어내지 않는다.
    """
    _report_usage(on_usage, meta, prompt_key="promptTokenCount",
                  read_key="cachedContentTokenCount", write_key="_없는칸",
                  out_key="candidatesTokenCount", cache_is_extra=False,
                  think_key="thoughtsTokenCount")
    # 생각 진행 — 이 계약의 누적 추정치가 그 칸이다. **새 어휘를 안 만든다**: 머리말이
    # 세운 `on_think` 계약(누적 추정 토큰)에 그대로 든다. 그 자리는 CLI 갈래가 먼저 섰고
    # 「나머지 셋은 낼 신호가 없다」였는데, 이제 요청하므로 이 계약이 그 자리에 든다.
    n = (meta or {}).get("thoughtsTokenCount")
    if on_think and isinstance(n, int):
        on_think(n)


def _text_of(content):
    """블록 목록으로 와도 글자 하나로 편다 — 이 어댑터의 마디는 글자뿐이다."""
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content or []
                   if isinstance(b, dict))


# ---------- 로컬 claude CLI 계약 — HTTP 가 아니다 ----------
# atelier app/providers.py 의 `_cli_once` 한 벌에서 가져와 깎았다 (커밋 d93df1d)


class CliLoginRequired(RuntimeError):
    """이 PC 의 claude CLI 가 로그인 안 돼 있다 — 사람이 창에서 해야 풀린다.

    ⚠ **일반 실패와 가르는 까닭은 화면이 할 일이 다르기 때문이다.** 다른 오류는 읽고 마는
      자리지만 이것은 **문 하나로 풀린다** — 서버가 그 문을 세울 수 있게 종류를 남긴다
      (서버 문의 로그인 안내).
    ⚠ **알아보는 자리가 여기인 까닭** — 이 문구는 CLI 가 쥔 남의 계약이다. 화면에서 글자를
      맞추면 계약이 바뀔 때 고칠 자리를 화면에서 찾게 된다. CLI 를 감싸는 이 어댑터가 그
      계약을 아는 유일한 자리다.
    """


# CLI 가 로그인 안 됐을 때 result 에 싣는 말. **부분 일치·소문자 비교** — 뒤에 붙는
# 안내(`Please run /login`)는 판마다 달라질 수 있어 앞머리만 잡는다.
_CLI_NOT_LOGGED_IN = "not logged in"

# 생각 진행을 싣고 오는 `system` 줄의 갈래 이름 — 그 줄의 `estimated_tokens` 가 누적
# 추정치다. **이 계약을 아는 자리가 여기 하나라** 낱말도 여기 산다.
_CLI_THINK = "thinking_tokens"

# 이 갈래의 시계가 **무엇에 걸렸나** — 갈라 들어야 하는 까닭은 뒷일이 달라서다. 침묵이면
# 아무것도 안 왔는데 우리가 죽인 것이라 오류로 세우고, 예산이면 HTTP 갈래가 하는 그대로
# **조용히 내려놓는다**(받아 둔 몫은 손에 남고 stop 이 빈다). 안 가르면 같은 사건이
# 갈래마다 다른 말로 기록에 남아 둘로 보인다.
_WALL_SILENT, _WALL_BUDGET = "침묵", "예산"

# 낱말은 **한 자리에서 짓는다** — 오류 문구와 `on_cut` 사유가 같은 사건을 두 말로 남기면
# 기록에 두 건으로 보인다.
CUT_CLI_RC = "claude CLI 가 {rc} 로 끝났다"
CUT_CLI_SILENT = "claude CLI 가 {secs}초를 잠잠해 우리가 끊었다"

# 옵션이 이 조합인 까닭 —
#   `--safe-mode`  : CLAUDE.md·스킬·훅·플러그인을 끄되 **인증은 살린다.** `--bare` 는
#                    OAuth·키체인을 아예 안 읽어 구독으로 못 붙는다
#   `--tools ""`   : 도구를 전부 끈다 — 우리가 원하는 것은 글이지 파일 조작이 아니다
#   `--no-session-persistence` : 쓰는 사람 디스크에 대화를 안 남긴다
_CLI_ARGS = ["-p", "--safe-mode", "--tools", "",
             "--no-session-persistence", "--verbose",
             "--output-format", "stream-json", "--include-partial-messages",
             "--input-format", "stream-json"]

# 접는 봉투의 첫 줄 — **지시문이 아니라 이 길의 포장이다.** CLI 의 기본 시스템 층이 「도구
# 있는 에이전트」로 말을 걸어, 도구를 다 꺼도 모델이 긴 글 앞에서 그 습관을 낸다(atelier
# 실사용 둘: Write 호출을 시도해 파싱 오류로 죽었고, 「파일에 조각으로 조립하겠다」는 서사가
# 본문에 섞였다). 그래서 접는 자리에서 그 틀을 되집는다.
_CLI_FRAME = ("[이 판의 계약] 파일 시스템도 도구도 없다 — Write·Bash 류를 부르거나 부르는 "
              "시늉을 내지 마라. 산출물이 아무리 길어도 **응답 본문의 글자로만** 낸다. "
              "길어서 끊기면 그대로 끊겨라 — 잇는 일은 네 몫이 아니다.")


class CliEnvelope(NamedTuple):
    """이 계약이 보낼 것 한 벌 — **주소도 머리도 키 자리도 없다.**

    ⚠ `Envelope` 와 다른 꼴인 것이 요점이다. 억지로 같은 칸에 앉히면 명세가 「주소:
      POST 」 같은 빈말을 찍는다 — 없는 것은 없는 채로 둔다.
    ⚠ **실행 파일의 실제 자리는 여기 안 든다** — PATH 는 부르는 순간 읽는다
      (`_cli_once`). 짓는 자리에서 찾으면 CLI 가 안 깔린 PC 에서 **드라이런 명세조차**
      못 짓는다.
    """
    args: list           # 고정 인자 + 모델
    payload: str         # stdin 으로 흘려보낼 stream-json 한 줄
    folded_chars: int    # 접힌 봉투가 몇 자인가 — 명세가 읽는 재료다


def _cli_envelope(layers, messages, c):
    """봉투 한 벌 → CLI stream-json 입력. **system 과 오간 턴을 하나로 접는다.**

    ⚠ **`--system-prompt` 로 안 싣고 사용자 메시지 앞에 접는 까닭이 둘이다**: 이 판의
      CLI 에는 시스템 글을 파일로 주는 길이 없는데 우리 봉투는 수만 자라 명령줄 한계
      (Windows 32,767자)를 넘고, Windows 에서 `claude` 는 `.CMD` 겉옷이라 긴 글을 인자로
      주면 cmd.exe 가 한 번 더 파싱해 깨진다. **길이로 갈래를 나누면 짧은 쪽만 검증되므로
      언제나 접는다.**
    ⚠ **대화도 한 덩이로 접는다.** stream-json 입력은 사람이 잇달아 말하는 자리라
      assistant 턴을 되돌려 넣는 길이 확실치 않다. 이 어댑터의 대화는 늘 「봉투 → 답 →
      이어서」 꼴이라 역할을 글로 적어 주면 읽힌다.
    """
    parts = [_CLI_FRAME]
    parts.extend(layers)
    for m in messages:
        text = _text_of(m["content"])
        parts.append(text if m["role"] == "user" else f"[지난 답변]\n{text}")
    folded = "\n\n".join(parts)
    payload = json.dumps({"type": "user",
                          "message": {"role": "user", "content": folded}})
    return CliEnvelope(args=list(_CLI_ARGS) + ["--model", c.model],
                       payload=payload,
                       folded_chars=len(folded))


def _cli_spec(env, c):
    """이 계약의 드라이런 명세 — **HTTP 명세와 칸이 다르다.**

    ⚠ 강제 드라이런(`gateway.DRY_RUN_FORCED`)이 아니면 이 갈래는 여기 안 온다 — 키가
      없어도 `local` 이 서서 실제로 부른다(`gateway.creds`). 그래도 자리를 두는 까닭은
      강제 드라이런이 **갈래를 안 가려야** 하기 때문이다: 한 갈래만 빠지면 「안 보낸다」를
      켜 놓고 그 갈래로 나간다.
    """
    return "\n".join([
        "[드라이런] 안 보냈다 — 강제 드라이런이다",
        f"갈래: {c.provider} · 계약: {c.contract} · 모델: {c.model}",
        f"부를 것: {gateway.CLI_EXE} {' '.join(env.args)}",
        f"주소: 없다 — 이 PC 에서 뜬다(끝점은 {gateway.CLI_API_URL})",
        f"자격: {'실어 온 토큰' if c.token else '이 PC 의 구독 로그인'}",
        "출력 상한: 실을 자리가 없다 — 모델이 스스로 멈춘다",
        f"접힌 봉투: {env.folded_chars}자 (stdin 으로 흘려보낸다)",
    ])


def _cli_evidence(tail):
    """오류 직전의 스트림 꼬리를 파일로 남기고 그 좌표를 돌려준다.

    「모델이 무슨 도구를 어떤 인자로 부르려 했나」 같은 사실은 이 꼬리에만 있다 — 아뜰리에
    2026-08-22 실사용: 도구 없는 판에서 「tool call could not be parsed」가 났는데 증거가 안
    남아 진단이 추론에 머물렀다. atelier `providers._cli_evidence` 에서 가져왔고 손으로
    따라간다. 남기다 실패하면 조용히 접는다 — 증거 기록이 본 오류를 가리면 안 된다.

    ⚠ **머리와 몸을 한 덩이로 붙인다.** 두 번 나눠 쓰면 겹친 손이 그 사이에 끼어 **남의
      꼬리에 내 머리가 달린 기록**이 남는다 — 증거가 증거를 망친다.
    ⚠ 자리는 기록 폴더(`gateway.LOGS_DIR`)다 — 산출물 폴더는 사람이 보고 커밋하는 검체
      자리일 수 있어 이 PC 의 것은 거기 안 둔다."""
    try:
        p = gateway.LOGS_DIR / "_cli_error.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%dT%H:%M:%S')}\n" + "\n".join(tail) + "\n")
        return f" (직전 스트림 {len(tail)}줄: logs/{p.name})"
    except OSError:
        return ""


def _kill_tree(proc):
    """자식을 **가지째** 죽인다 — Windows 의 `claude` 는 `.CMD` 겉옷이라 우리가 쥔 것은
    cmd.exe 고 진짜 일꾼(node)은 그 아래다. cmd.exe 만 죽이면 일꾼이 산 채로 stdout 쓰기
    손잡이를 쥐고 있어 읽기 반복문이 영영 안 풀린다 — 시계가 죽였는데 화면에는 「도는 중」
    그대로다(아뜰리에 `cli_pipe_check` ③④가 Windows 에서 잡았다). POSIX 는 겉옷이 없어
    kill 하나면 된다.
    """
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False)
    else:
        proc.kill()


def _cli_why(walled, rc, err):
    """이 한 바퀴가 **왜 제대로 안 끝났나** — 한 줄로. 성했으면 빈 글자.

    ⚠ **오르는 자리와 터지는 자리는 다르다.** 한 글자도 못 받은 판은 부르는 쪽이 예외로
      받으므로 여기 올 일이 없고, 이 자가 서는 것은 **글자를 받아 두고도 제대로 안 끝난
      판**이다 — HTTP 갈래의 `_sse_events` 가 「받은 게 있으면 삼키되 사유는 넘긴다」로 서
      있는 그 자리다.
    ⚠ **셋을 한 줄로 잇되 시간 벽이 종료 코드보다 앞이다.** 우리가 죽인 자식은 0 이 아닌
      값으로 끝나므로 코드를 먼저 보면 **우리 시계가 운 자리가 「저쪽이 죽었다」로 적힌다.**
    ⚠ **길이는 HTTP 와 같은 자로 자른다**(`_CUT_WHY_CAP`) — 자식 stderr 가 봉투째 오면 그
      한 줄이 도로 기록을 덮는다.
    """
    if walled:
        why = (CUT_BUDGET if walled[0] == _WALL_BUDGET
               else CUT_CLI_SILENT.format(secs=gateway.TIMEOUT_S))
    elif rc:
        why = CUT_CLI_RC.format(rc=rc)
    else:
        return ""
    said = " ".join((err or "").split())
    return (f"{why}: {said}" if said else why)[:_CUT_WHY_CAP]


def _cli_once(env, c, on_text, on_usage, deadline, on_cut, on_think=None):
    """이 PC 에 깔린 claude CLI 를 파이프로 부른다 — 구독 인증을 그대로 빌린다.

    HTTP 가 아니지만 돌려주는 것은 같다: `(이어붙인 글자, stop_reason)`. 출력이
    **Anthropic SSE 와 같은 모양**이라(`{"type":"stream_event","event":{…}}`) 한 겹만
    벗기면 저 갈래의 이벤트 처리를 그대로 쓴다.

    ⚠ **시계는 손으로 지고, 재는 것은 침묵이다** — HTTP 갈래 셋은 `urlopen(timeout=…)` 이
      지는데 그것은 소켓 자라 읽기마다 다시 센다. 여기는 파이프라 아무도 안 지므로
      `gateway.TIMEOUT_S` 로 같은 자를 세우되 같은 어법으로 잰다: 무슨 줄이든 오는 동안은
      산 것이고, 그만큼 잠잠하면 죽인다. 총 시간으로 재면 생각 구간이 긴 판을 「아무것도
      안 냈다」로 죽인다.
      ⚠ **침묵 하나로는 상한이 안 선다** — 조각이 계속 오면 영영 안 우는 자다. 부르는
        쪽이 `deadline` 을 주면 그것과 **먼저 오는 쪽**으로 눕는다(`_sock_timeout` 과 같은
        규율을 손으로 진 것이다).
    ⚠ **생각(thinking)은 글자가 아니라 진행이다** — 이 CLI 는 생각을 스스로 켜고, 그동안
      text_delta 는 한 조각도 안 온다. 그 신호를 **살아 있음으로 세지 않으면** 생각이 긴
      판이 침묵으로 몰려 죽는다. 누적 추정치는 `on_think` 로 나가 화면의 정적을 메운다
      (AI-prompt-helper 결정 0030) — 계약 넷 중 그 줄을 내는 것은 이 갈래 하나다.
    ⚠ **출력 상한을 지정할 길이 없다** — `c.max_tokens` 가 여기서는 안 걸린다. 모델이
      스스로 멈추고, 이어받기는 stop_reason 이 그대로 든다.
    """
    exe = shutil.which(gateway.CLI_EXE)
    if not exe:
        raise RuntimeError(
            f"이 PC 에서 {gateway.CLI_EXE} CLI 를 못 찾았다 — PATH 를 확인한다")
    # 자격을 실어 왔으면 **그 사람 구독으로** 돈다 — CLI 가 이 이름을 이 PC 의 로그인보다
    # 앞세운다. 안 실어 왔으면 물리지 않고 이 PC 의 로그인이 그대로 쓰인다 — 그 자리를
    # 앞자리로 좁히는 것은 서버의 자격 문이 든다. 토큰은 여기서도 어디에도 안 적힌다.
    penv = {**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": c.token} if c.token else None
    proc = subprocess.Popen([exe] + env.args, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace", env=penv)

    # ⚠ **쓰기 하나·읽기 둘을 한 줄기로 하면 맞물려 선다.** 봉투가 수만 자인데 한글은
    #   UTF-8 로 글자당 서너 바이트라 OS 파이프 버퍼(보통 64KB)를 훌쩍 넘고, `--verbose` 로
    #   띄운 자식도 stdin 을 다 읽기 전에 로그를 흘린다. 그러면 부모는 stdin 을 다 못 쓴 채
    #   막히고 자식은 안 읽히는 stdout·stderr 에 막혀 **서로 상대를 기다린다** — 오류도 안
    #   나고 영영 안 끝난다. 곁줄기 둘로 갈라 셋이 동시에 흐르게 한다.
    def _feed():
        try:
            proc.stdin.write(env.payload + "\n")
            proc.stdin.close()
        except OSError:
            pass        # 자식이 먼저 죽으면 끊긴다 — 판정은 아래 returncode 가 든다

    err_parts = []

    def _drain():
        try:
            err_parts.append(proc.stderr.read() or "")
        except OSError:
            pass

    threading.Thread(target=_feed, daemon=True).start()
    drainer = threading.Thread(target=_drain, daemon=True)
    drainer.start()

    walled, alive, clock = [], [time.monotonic()], [None]

    def _left():
        """다음에 깰 때까지 — 침묵 시계와 남은 예산 중 **먼저 오는 쪽**."""
        left = gateway.TIMEOUT_S - (time.monotonic() - alive[0])
        if deadline is not None:
            left = min(left, deadline - time.monotonic())
        return left

    def _wall():
        left = _left()
        if left > 0:
            # 줄이 올 때마다 `alive` 가 되감기므로, 방금 왔으면 남은 시간이 양수다 —
            # 그만큼 뒤로 다시 눕는다. **헛죽임이 없다.**
            clock[0] = threading.Timer(left, _wall)
            clock[0].daemon = True
            clock[0].start()
            return
        # **무엇에 걸렸나를 여기서 이름 부른다** — 깨어난 자리에서만 갈리고, 아래 마무리가
        # 그 이름으로 오류를 세울지 조용히 내려놓을지 정한다.
        walled.append(_WALL_BUDGET
                      if deadline is not None and time.monotonic() >= deadline
                      else _WALL_SILENT)
        _kill_tree(proc)

    clock[0] = threading.Timer(max(_left(), _WALL_FLOOR_S), _wall)
    clock[0].daemon = True
    clock[0].start()

    out, stop = [], None
    # 자식이 스스로 이어 쓴 자리 — `message_start` 가 둘째부터면 앞 메시지가 출력 상한에서
    # 잘려 CLI 가 이은 것이다. 우리 봉합(`stream_resumed`)은 이 안을 못 보므로 여기서
    # 이음매를 적어 두고(`seams` — `out` 의 자리) 끝에 `_join_seams` 가 벗긴다. 같은 CLI 를
    # 같은 인자(`_CLI_ARGS`)로 부르므로 아뜰리에가 겪은 자리(#335)가 여기서도 난다.
    # ⚠ **안 든 것 하나** — 아뜰리에는 바퀴 줄에 「안에서 메시지 몇」을 씀씀이 칸(`messages`)
    #   으로 싣는다. 기록층이 그 칸을 읽는 앱만 얹는다 — 씨앗은 안 든다(안 쓰는 칸이다).
    seams, msgs = [], [0]
    tail = []          # 마지막 몇 줄 — 오류가 나면 「무슨 일이 오갔나」의 유일한 증거다
    try:
        for line in proc.stdout:
            alive[0] = time.monotonic()   # 로그든 생각이든, 말하는 자식은 산 자식이다
            line = line.strip()
            if not line:
                continue
            tail.append(line[:600])
            if len(tail) > 8:
                del tail[0]
            try:
                msg = json.loads(line)
            except ValueError:
                continue                  # 로그 줄 등 JSON 아닌 것은 흘린다
            kind = msg.get("type")
            if kind == "stream_event":
                ev = msg.get("event") or {}
                if ev.get("type") == "message_start":
                    msgs[0] += 1
                    if msgs[0] > 1:
                        seams.append(len(out))
                    _report_usage(on_usage, (ev.get("message") or {}).get("usage"))
                elif ev.get("type") == "content_block_delta":
                    piece = (ev.get("delta") or {}).get("text", "")
                    if piece:
                        out.append(piece)
                        if on_text:
                            on_text(piece)
                elif ev.get("type") == "message_delta":
                    stop = (ev.get("delta") or {}).get("stop_reason") or stop
                    _report_usage(on_usage, ev.get("usage"))
            elif kind == "system" and msg.get("subtype") == _CLI_THINK:
                # **생각 진행** — 누적 추정치를 그대로 넘긴다(AI-prompt-helper 결정 0030).
                # ⚠ **`stream_event` 쪽 `thinking_delta` 를 안 읽는 까닭** — 이 CLI 는 생각
                #   본문을 비워 보내고(가림) 증분이 `null` 로도 와서, 그 줄로는 셈이 안
                #   선다. 아뜰리에가 같은 CLI·같은 인자에서 실측한 자리를 그대로 든다
                #   (저쪽 `providers._cli_once` · 결정 0115) — **이 저장소는 아직 진짜
                #   `claude` 를 한 번도 안 불렀다.**
                n = msg.get("estimated_tokens")
                if on_think and isinstance(n, int):
                    on_think(n)
            elif kind == "result":
                # 마지막 한 줄이 판정을 든다 — 거부·한도 초과는 여기서만 보인다.
                stop = msg.get("stop_reason") or stop
                if msg.get("is_error"):
                    said = msg.get("result") or "알 수 없는 오류"
                    if _CLI_NOT_LOGGED_IN in said.lower():
                        raise CliLoginRequired("이 PC 의 Claude 가 로그인돼 있지 않아요"
                                               + _cli_evidence(tail))
                    raise RuntimeError(f"claude CLI: {said}" + _cli_evidence(tail))
    except BaseException:
        _kill_tree(proc)        # 시계는 곧 꺼진다 — 여기서 안 죽이면 자식이 남는다
        raise
    finally:
        clock[0].cancel()

    # 2초 — 이미 죽은 자식의 stderr 를 퍼내던 스레드를 거두는 자리다. 값이 아니라
    # **안 매달리는 것**이 요점이라 이름을 안 준다: 늦으면 그 꼬리를 포기하고 간다.
    drainer.join(timeout=2)
    err = "".join(err_parts)[:500]
    rc = proc.wait()
    if walled and not out:
        # 침묵이면 오류다 — 한 글자도 안 왔고 이어붙일 것이 없다. 예산이면 **조용히
        # 내려놓는다**: 왜 멈췄나를 예산 쥔 쪽이 이미 안다. 여기서 오류를 세우면 같은
        # 사건이 갈래마다 다른 말로 남는다.
        if walled[0] == _WALL_SILENT:
            raise RuntimeError(
                CUT_CLI_SILENT.format(secs=gateway.TIMEOUT_S) + f": {err}")
    elif rc != 0 and not out:
        # ⚠ **`elif` 다.** 우리가 죽인 자식은 0 이 아닌 값으로 끝나므로, 나란히 두면 예산에
        #   걸린 자리가 여기서 「rc 로 끝났다」로 도로 오류가 된다.
        raise RuntimeError(f"{CUT_CLI_RC.format(rc=rc)}: {err}")
    # **받아 두고도 제대로 안 끝난 판은 사유를 올린다.** 여기까지 왔다는 것은 글자가 손에
    # 있다는 뜻이라 위 둘이 안 터졌다 — 그러면 rc·자식 stderr·시간 벽이 셋 다 버려지고,
    # 죽은 자식이 `stop=None` 으로 포장돼 이어받기가 걸리는데 왜 멈췄나는 아무 데도 안
    # 남는다. HTTP 갈래는 같은 자리를 `on_cut` 으로 올린다 — **같은 일을 하는 갈래를
    # 반대로 두지 않는다.**
    if on_cut:
        why = _cli_why(walled, rc, err)
        if why:
            on_cut(why)
    return _join_seams(out, seams), stop


# ---------- 계약 → 그 계약을 아는 함수 ----------
# 표로 둔다. if/else 로 두면 새 계약을 단 사람이 **한 줄을 빠뜨려도 조용히 딴 데로
# 떨어진다.** 표는 없는 이름이 오면 그 자리에서 선다.

_ENV_BY_CONTRACT = {
    gateway.CONTRACT_ANTHROPIC: _ant_envelope,
    gateway.CONTRACT_OPENAI: _oa_envelope,
    gateway.CONTRACT_GEMINI: _gm_envelope,
    gateway.CONTRACT_CLI: _cli_envelope,
}
_BY_CONTRACT = {
    gateway.CONTRACT_ANTHROPIC: _anthropic_once,
    gateway.CONTRACT_OPENAI: _openai_once,
    gateway.CONTRACT_GEMINI: _gemini_once,
    gateway.CONTRACT_CLI: _cli_once,
}
# 드라이런 명세도 **계약마다 갈린다** — HTTP 셋은 주소·머리·본문을 찍고, CLI 는 그 셋이
# 아예 없다. 한 함수에 넣으면 없는 칸을 빈 값으로 찍어 **명세가 거짓말을 한다.**
_SPEC_BY_CONTRACT = {
    gateway.CONTRACT_ANTHROPIC: spec,
    gateway.CONTRACT_OPENAI: spec,
    gateway.CONTRACT_GEMINI: spec,
    gateway.CONTRACT_CLI: _cli_spec,
}
