"""그림 끌어내기 검사 — 프록시가 `tool_result` 안의 `image` 를 **열리는 자리로** 옮기나.

`hoist_tool_result_images` 를 직접 불러 잰다 — 망도 가짜 게이트웨이도 안 쓴다. 이 보정의
판정 대상은 **본문의 모양**이고, 그 모양이 맞으면 게이트웨이가 보는 것은 이미 실측됐다
(claude-config #76 · 눈가림 프로브 두 판).

    python -X utf8 hoist_check.py

⚠ **양방향이다.** 옮기는 것만 재면 「아무것도 안 건드리는 자리까지 건드리는」 결함이 안 잡힌다 —
  그림 없는 `tool_result` · 글자만 든 대화 · user 아닌 메시지는 **바이트 하나 안 바뀌어야** 한다.
⚠ **자리를 잰다 — 장수만 세지 않는다.** 그림이 옮겨진 것과 `tool_result` **뒤**에 놓인 것은
  다른 명제고, 앞에 놓이면 게이트웨이가 400 을 낸다(실측). 그래서 색인을 견준다.
⚠ **검체는 실물 모양이다.** Claude Code 의 `Read` 는 `tool_result` 를 **마지막** 메시지에 싣고
  그 안에 [text, image] 를 넣는다 — 그 꼴이 ①이다. 뒤에 user 가 붙은 꼴도 같이 잰다.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from opus5_proxy import hoist_tool_result_images  # noqa: E402

IMG = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}}
IMG2 = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "BBBB"}}


def result(uid: str, *inner: object) -> dict:
    return {"type": "tool_result", "tool_use_id": uid, "content": list(inner)}


def use(uid: str) -> dict:
    return {"role": "assistant", "content": [{"type": "tool_use", "id": uid, "name": "view", "input": {}}]}


def blocks_of(messages: list, index: int) -> list:
    return messages[index]["content"]


def kinds(blocks: list) -> list[str]:
    return [b.get("type") for b in blocks if isinstance(b, dict)]


FAILED: list[str] = []


def check(name: str, ok: bool, saw: object = None) -> None:
    if ok:
        print("OK   %s" % name)
        return
    FAILED.append(name)
    print("FAIL %s%s" % (name, "" if saw is None else "  (봤다: %r)" % (saw,)))


# ── ① 실물 꼴 — `tool_result` 가 마지막이고 그 안에 [text, image] ─────────────────────
msgs = [{"role": "user", "content": [{"type": "text", "text": "봐라"}]},
        use("tu_1"),
        {"role": "user", "content": [result("tu_1", {"type": "text", "text": "그림"}, IMG)]}]
moved = hoist_tool_result_images(msgs)
tail = blocks_of(msgs, 2)
check("① 실물 꼴 — 한 장 옮겼다", moved == 1, moved)
check("① 메시지 수가 안 늘었다", len(msgs) == 3, len(msgs))
check("① 그림이 tool_result **뒤**에 섰다", kinds(tail) == ["tool_result", "image"], kinds(tail))
check("① tool_result 안에 그림이 안 남았다",
      kinds(tail[0]["content"]) == ["text", "text"], kinds(tail[0]["content"]))
check("① 자리표시가 tool_use_id 를 든다", "tu_1" in tail[0]["content"][-1]["text"],
      tail[0]["content"][-1]["text"])

# ── ② tool_result 가 여럿 · 그림도 여럿 ────────────────────────────────────────────
msgs = [{"role": "user", "content": [{"type": "text", "text": "봐라"}]},
        use("tu_1"),
        {"role": "user", "content": [result("tu_1", IMG), result("tu_2", IMG2)]}]
moved = hoist_tool_result_images(msgs)
tail = blocks_of(msgs, 2)
check("② 두 장 옮겼다", moved == 2, moved)
check("② 두 tool_result 가 다 앞에 남았다",
      kinds(tail) == ["tool_result", "tool_result", "image", "image"], kinds(tail))
check("② 그림 순서가 tool_result 순서다",
      [b["source"]["data"] for b in tail[2:]] == ["AAAA", "BBBB"],
      [b["source"]["data"] for b in tail[2:]])
check("② 자리표시가 서로 다른 id 를 든다",
      "tu_1" in tail[0]["content"][-1]["text"] and "tu_2" in tail[1]["content"][-1]["text"])

# ── ③ 한 tool_result 에 그림 둘 — 장수를 글자에 댄다 ────────────────────────────────
msgs = [{"role": "user", "content": [result("tu_1", IMG, IMG2)]}]
moved = hoist_tool_result_images(msgs)
note = blocks_of(msgs, 0)[0]["content"][-1]["text"]
check("③ 두 장 옮겼다", moved == 2, moved)
check("③ 자리표시가 「그림 2장」이라 적는다", "2장" in note, note)

# ── ④ 뒤에 user 가 붙은 꼴 — 그 메시지는 안 건드린다 ──────────────────────────────
msgs = [use("tu_1"),
        {"role": "user", "content": [result("tu_1", IMG)]},
        {"role": "user", "content": [{"type": "text", "text": "그래서?"}]}]
before_next = copy.deepcopy(msgs[2])
moved = hoist_tool_result_images(msgs)
check("④ 한 장 옮겼다", moved == 1, moved)
check("④ 그림이 **제 메시지** 안에 섰다",
      kinds(blocks_of(msgs, 1)) == ["tool_result", "image"], kinds(blocks_of(msgs, 1)))
check("④ 다음 user 메시지는 안 건드렸다", msgs[2] == before_next, msgs[2])

# ── 음성 — 아무것도 안 바뀌어야 하는 자리들 ─────────────────────────────────────────
NEGATIVE = [
    ("그림 없는 tool_result",
     [{"role": "user", "content": [result("tu_1", {"type": "text", "text": "됐다"})]}]),
    ("tool_result 가 없는 대화",
     [{"role": "user", "content": [{"type": "text", "text": "안녕"}, IMG]}]),
    ("assistant 메시지 안의 블록",
     [{"role": "assistant", "content": [result("tu_1", IMG)]}]),
    ("content 가 글자인 메시지",
     [{"role": "user", "content": "그냥 글자"}]),
    ("tool_result.content 가 글자",
     [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu_1", "content": "글자"}]}]),
    ("메시지가 dict 가 아닌 것이 섞임", ["부스러기", {"role": "user", "content": [IMG]}]),
]
for label, sample in NEGATIVE:
    before = copy.deepcopy(sample)
    moved = hoist_tool_result_images(sample)
    check("음성 · %s — 0 장" % label, moved == 0, moved)
    check("음성 · %s — 본문이 그대로다" % label, sample == before, sample)

# ── 양성 대조 — 검사가 정말 재고 있나 ───────────────────────────────────────────────
#   ⚠ 초록만 보고 「검사가 있다」로 읽지 않는다. 옮기지 **않은** 본문을 같은 자로 재서
#     빨강이 나는 것까지 봐야 이 파일이 무언가를 재고 있다는 것이 선다.
unmoved = [{"role": "user", "content": [result("tu_1", {"type": "text", "text": "그림"}, IMG)]}]
check("양성 대조 — 안 옮긴 본문은 「뒤에 섰다」를 통과 못 한다",
      kinds(blocks_of(unmoved, 0)) != ["tool_result", "image"])

print()
if FAILED:
    print("어긋남 %d" % len(FAILED))
    for name in FAILED:
        print("  · %s" % name)
    sys.exit(1)
print("어긋남 0 · 못 잰 층 없음")
