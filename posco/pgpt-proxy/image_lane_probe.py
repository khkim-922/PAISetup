"""게이트웨이가 `tool_result` 안의 그림을 **정말 못 받는가** — 우회 갈래를 여럿 재는 눈가림 프로브.

왜 재나: `tool_result` 안의 `image` 가 삼켜지는 것은 실측됐다(#76). 그런데 「삼킨다」와
「어떤 꼴로도 못 받는다」는 다른 명제다 — 상류 겹이 뭘 보고 버리는지 모르는 채 프록시
보정을 굳히면, 실은 열려 있던 문을 못 본 채 우회를 껴안는다.

여기서 재는 갈래 — 다 같은 그림·같은 답이라 판정이 깨끗하다:
  ① `tool_result.content` 가 **블록 배열**  — 지금 Read 의 길 (대조군)
  ② `tool_result` 를 통째로 **쓰지 않고** user 블록   — 프록시가 할 일 (양성 대조)
  ③ `tool_result.content` 에 image 하나만 (text 없이)
  ④ `tool_result` **뒤 별개 user 메시지**에 그림
  ⑤ OpenAI 라우트(`/v1/chat/completions`)의 `role: tool` + 뒤따르는 user image_url

⚠ 눈가림이다 — 정답은 곁 파일에만 적고 화면에 안 찍는다. 아는 값을 맞히는 것은 재는 것이 아니다.
⚠ **한 그림·한 정답으로 모든 갈래를 잰다** — 갈래마다 다른 그림을 쓰면 「못 맞혔다」가 갈래
  탓인지 그림 탓인지 안 갈린다.
"""
import base64
import json
import os
import random
import struct
import sys
import urllib.error
import urllib.request
import zlib

W = H = 320
SHAPES = ('왼쪽 절반', '오른쪽 아래 사분면', '가운데 가로 띠', '대각선 띠')
COLORS = {'빨강': (220, 30, 30), '파랑': (30, 60, 220), '초록': (30, 170, 60), '노랑': (240, 200, 20)}
ASK = ('이 그림에서 ① 칠한 색과 ② 칠한 자리(왼쪽 절반 · 오른쪽 아래 사분면 · '
       '가운데 가로 띠 · 대각선 띠 중 하나)를 대라. 딴말 없이 「색 · 자리」 꼴로.')
VIEW = {'name': 'view', 'description': '그림을 돌려준다',
        'input_schema': {'type': 'object', 'properties': {}, 'required': []}}
VIEW_OAI = {'type': 'function', 'function': {'name': 'view', 'description': '그림을 돌려준다',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}}}


def bake():
    """답을 모르는 그림 하나 — (PNG 바이트, 정답 글자)."""
    shape = random.choice(SHAPES)
    name = random.choice(list(COLORS))
    c, bg = COLORS[name], (250, 250, 250)
    rows = []
    for y in range(H):
        row = bytearray(b'\x00')
        for x in range(W):
            if shape == '왼쪽 절반':
                hit = x < W // 2
            elif shape == '오른쪽 아래 사분면':
                hit = x >= W // 2 and y >= H // 2
            elif shape == '가운데 가로 띠':
                hit = H // 3 <= y < 2 * H // 3
            else:
                hit = abs(x - y) < 40
            row += bytes(c if hit else bg)
        rows.append(bytes(row))

    def ch(tag, data):
        body = tag + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)

    png = (b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
           + ch(b'IDAT', zlib.compress(b''.join(rows))) + ch(b'IEND', b''))
    return png, '%s · %s' % (name, shape)


BASE = os.environ['ANTHROPIC_BASE_URL'].rstrip('/')
TOK = os.environ['ANTHROPIC_AUTH_TOKEN']


def call(path, body):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOK,
                 'anthropic-version': '2023-06-01'})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            d = json.load(r)
        if 'choices' in d:   # OpenAI 꼴
            msg = (d['choices'][0] or {}).get('message') or {}
            return r.status, str(msg.get('content') or '').strip(), d.get('usage', {})
        txt = ' '.join(b.get('text', '') for b in d.get('content', []) if b.get('type') == 'text')
        return r.status, txt.strip(), d.get('usage', {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:200], {}
    except Exception as e:  # noqa: BLE001 — 「못 쟀다」도 결과다
        return 0, '%s: %s' % (type(e).__name__, e), {}


def img(b64):
    return {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': b64}}


def lanes(b64, model, oai_model):
    """(표찰, 경로, 본문) 목록 — 다 같은 그림을 묻는다."""
    ask_tool = 'view 를 불러 그림을 받고 ' + ASK
    turn1 = {'role': 'user', 'content': [{'type': 'text', 'text': ask_tool}]}
    use = {'role': 'assistant', 'content': [{'type': 'tool_use', 'id': 'tu_1', 'name': 'view', 'input': {}}]}

    def anth(messages, **extra):
        body = {'model': model, 'max_tokens': 128, 'messages': messages}
        body.update(extra)
        return ('/v1/messages', body)

    out = [
        ('① tool_result 안 (지금 Read 의 길)', *anth([turn1, use, {'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': 'tu_1',
             'content': [{'type': 'text', 'text': '그림 1장'}, img(b64)]}]}], tools=[VIEW])),

        ('② 도구 없이 user 블록 (프록시가 할 일)', *anth([
            {'role': 'user', 'content': [{'type': 'text', 'text': ASK}, img(b64)]}])),

        ('③ tool_result 안 · image 하나만', *anth([turn1, use, {'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': 'tu_1', 'content': [img(b64)]}]}], tools=[VIEW])),

        ('④ tool_result 뒤 별개 user 메시지', *anth([turn1, use,
            {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'tu_1',
                                          'content': [{'type': 'text', 'text': '그림은 다음 메시지에'}]}]},
            {'role': 'user', 'content': [img(b64), {'type': 'text', 'text': ASK}]}], tools=[VIEW])),
    ]
    if oai_model:
        out.append(('⑤ OpenAI 라우트 · role:tool + 뒤따르는 image_url',
                    '/v1/chat/completions', {
                        'model': oai_model, 'max_tokens': 128, 'tools': [VIEW_OAI], 'messages': [
                            {'role': 'user', 'content': ask_tool},
                            {'role': 'assistant', 'content': None, 'tool_calls': [
                                {'id': 'call_1', 'type': 'function',
                                 'function': {'name': 'view', 'arguments': '{}'}}]},
                            {'role': 'tool', 'tool_call_id': 'call_1', 'content': '그림은 다음 메시지에'},
                            {'role': 'user', 'content': [
                                {'type': 'text', 'text': ASK},
                                {'type': 'image_url',
                                 'image_url': {'url': 'data:image/png;base64,' + b64, 'detail': 'auto'}}]}]}))
    return out


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else 'claude-opus-5'
    oai = sys.argv[2] if len(sys.argv) > 2 else ''
    png, answer = bake()
    b64 = base64.b64encode(png).decode()
    with open(os.path.join(os.environ.get('TEMP', '.'), 'hoist-answer.txt'), 'w', encoding='utf-8') as f:
        f.write(answer)
    print('모델 %s%s · 그림 %d×%d · 정답은 곁 파일에만 적었다'
          % (model, (' · OpenAI ' + oai) if oai else '', W, H))
    print()
    for label, path, body in lanes(b64, model, oai):
        st, txt, usage = call(path, body)
        print('%s\n   상태 %s · 입력토큰 %s\n   답: %s\n'
              % (label, st, usage.get('input_tokens', usage.get('prompt_tokens', '?')), txt[:160]))


if __name__ == '__main__':
    main()
