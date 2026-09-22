"""`tool_result` 가 **마지막**일 때 그림을 어떻게 보내야 보나 — ④의 남은 구멍을 잰다.

왜 재나: `hoist_tool_result_images` 는 「뒤따르는 user 메시지」에 그림을 얹는데, Claude Code 의
`Read` 가 만드는 실제 대화는 **`tool_result` 가 마지막**이다(도구 결과를 받고 모델이 답할 차례).
그러면 옮길 자리가 없어 함수가 아무것도 안 하고, 사내에서 `Read` 는 여전히 못 본다.

⚠ 이 프로브가 재는 것은 「그 자리를 어떻게 여나」다. 갈래마다 대화를 **지어내는 정도**가 달라,
  통하는 것과 정당한 것이 갈릴 수 있다 — 통하는 것부터 재고 고르는 것은 사람이 든다.
⚠ 눈가림 — 정답은 곁 파일에만 적는다.
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


def bake():
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


def call(body):
    req = urllib.request.Request(
        BASE + '/v1/messages', data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + TOK,
                 'anthropic-version': '2023-06-01'})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            d = json.load(r)
        txt = ' '.join(b.get('text', '') for b in d.get('content', []) if b.get('type') == 'text')
        return r.status, txt.strip(), d.get('usage', {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:200], {}
    except Exception as e:  # noqa: BLE001
        return 0, '%s: %s' % (type(e).__name__, e), {}


def img(b64):
    return {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': b64}}


def lanes(b64, model):
    """`tool_result` 가 마지막인 실제 대화에서, 그림을 어디에 두면 보나."""
    ask_tool = 'view 를 불러 그림을 받고 ' + ASK
    turn1 = {'role': 'user', 'content': [{'type': 'text', 'text': ask_tool}]}
    use = {'role': 'assistant', 'content': [{'type': 'tool_use', 'id': 'tu_1', 'name': 'view', 'input': {}}]}
    moved = {'type': 'tool_result', 'tool_use_id': 'tu_1',
             'content': [{'type': 'text', 'text': '[그림은 곁에 실려 있다]'}]}

    def anth(messages):
        return {'model': model, 'max_tokens': 128, 'tools': [VIEW], 'messages': messages}

    return [
        # ㉠ 대조군 — 고치기 전 그대로. 못 봐야 판정이 성립한다
        ('㉠ tool_result 안 (대조군 · 못 봐야 맞다)',
         anth([turn1, use, {'role': 'user', 'content': [
             {'type': 'tool_result', 'tool_use_id': 'tu_1',
              'content': [{'type': 'text', 'text': '그림'}, img(b64)]}]}])),

        # ㉡ 같은 메시지 안에서 tool_result 옆으로 — 메시지를 안 늘린다
        ('㉡ 같은 user 메시지 · tool_result 뒤에 그림 블록',
         anth([turn1, use, {'role': 'user', 'content': [moved, img(b64)]}])),

        # ㉢ 같은 메시지 · 그림을 tool_result **앞**에
        ('㉢ 같은 user 메시지 · tool_result 앞에 그림 블록',
         anth([turn1, use, {'role': 'user', 'content': [img(b64), moved]}])),

        # ㉣ 그림 + 다시 묻는 글자까지 한 메시지에
        ('㉣ 같은 user 메시지 · 그림 + 물음 글자',
         anth([turn1, use, {'role': 'user', 'content': [
             moved, img(b64), {'type': 'text', 'text': ASK}]}])),
    ]


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else 'claude-opus-5'
    png, answer = bake()
    b64 = base64.b64encode(png).decode()
    with open(os.path.join(os.environ.get('TEMP', '.'), 'tail-answer.txt'), 'w', encoding='utf-8') as f:
        f.write(answer)
    print('모델 %s · 그림 %d×%d · tool_result 가 **마지막**인 대화 · 정답은 곁 파일에만' % (model, W, H))
    print()
    for label, body in lanes(b64, model):
        st, txt, usage = call(body)
        print('%s\n   상태 %s · 입력토큰 %s\n   답: %s\n'
              % (label, st, usage.get('input_tokens', '?'), txt[:160]))


if __name__ == '__main__':
    main()
