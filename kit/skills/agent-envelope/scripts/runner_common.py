"""맡기기 러너 셋(agy-background · codex-copilot-background · claude-background)이 함께 쓰는 손 — 인자 가르기 · 프롬프트
파일 풀기 · 답 파일 쓰기 · 끝 줄 · 도움말 · 프로세스 끊기. 띄우는 명령 · 갈래 판정 · 끝 줄의 칸 · 종료 코드 표처럼 러너마다
갈리는 것은 러너가 든다.

부르는 꼴 — 러너는 스킬 홈에 이 스킬과 나란히 깔린다::

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'agent-envelope' / 'scripts'))
    import runner_common as common
    common.main(build_parser, help_epilog, run, FOOTER, EXIT)

러너는 창 없이 돌아 말할 곳이 답 파일(`--out`)뿐이다 — 이 파일을 못 실으면 러너가 제 손으로 그 파일에 끝 줄을 남긴다.
"""
import argparse
import codecs
import json
import os
import subprocess
import sys
import traceback

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
DEFAULT_TIMEOUT_SEC = 1800      # 기본 한도 — 짧은 일도 그대로 둔다(끝나는 대로 돌아온다)
POLL_SEC = 2                    # 받는 쪽이 끝났나 보는 간격
STDERR_TAIL_CHARS = 2000        # 실패 때 답 파일에 옮기는 stderr 꼬리
SHIM_EXT = ('.cmd', '.bat')     # npm 이 윈도에 까는 실행 껍데기 — 그 곁의 JS 를 node 로 바로 띄운다
# 프롬프트 파일이 받는 인코딩 — `decode_prompt` 가 받는 것과 같은 말이고 거절 사유 · `--help` 가 이 글을 읽는다
PROMPT_ENCODINGS = 'UTF-8(BOM 은 있어도 없어도) · UTF-16 LE/BE(BOM 이 있어야)'
# 답 파일의 인코딩 — 윈도는 BOM 을 단다(PowerShell 5.1 `Get-Content` 는 BOM 없는 파일을 ANSI 로 읽어 한글 · `·` 를 깨뜨린다).
# 다른 OS 는 BOM 없이 둔다 — 첫 줄을 끝 줄 머리(`^[…-bg]`)로 찾는 손을 BOM 이 헛짚게 한다
ANSWER_ENCODING = 'utf-8-sig' if os.name == 'nt' else 'utf-8'


def write(path, text):
    """답 파일을 쓴다 — 인코딩은 `ANSWER_ENCODING`."""
    with open(path, 'w', encoding=ANSWER_ENCODING) as f:
        f.write(text)


class Usage(Exception):
    """인자를 못 갈랐다. argparse 는 그 말을 stderr 에 찍고 끝내지만 부른 쪽은 답 파일만 읽는다 — 답 파일에 옮긴다."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


class HelpFormat(argparse.RawDescriptionHelpFormatter):
    """`--help` 의 꼴 — 폭만 넓혀 플래그마다 한 줄에 둔다(아래쪽 절은 러너의 `help_epilog` 가 짠 그대로 간다)."""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=26, width=140)


def out_arg(args):
    """인자를 못 갈랐을 때 답 파일 자리 — `--out <경로>` · `--out=<경로>` 만 찾는다. 없으면 None."""
    for i, x in enumerate(args):
        if x == '--out' and i + 1 < len(args):
            return args[i + 1]
        if x.startswith('--out='):
            return x[len('--out='):]
    return None


def decode_prompt(raw):
    """프롬프트 파일 바이트 → 글. 받는 인코딩은 `PROMPT_ENCODINGS` — 그 밖이면 UnicodeDecodeError. BOM 은 걷힌다.
    글에 NUL 이 있어도 거절한다: BOM 없는 UTF-16 · BOM 있는 UTF-32 는 UTF-8 로도 읽혀 NUL 이 낀 채 받는 쪽으로 간다."""
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        text = raw.decode('utf-16')
    else:
        text = raw.decode('utf-8-sig')
    if '\x00' in text:
        raise UnicodeDecodeError('utf-8', raw, 0, len(raw), 'NUL 문자가 든다')
    return text


def kill_tree(proc):
    """띄운 프로세스와 그 밑 자식까지 같이 끊는다 — 머리만 끊으면 자식이 남는다."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)],
                       capture_output=True, creationflags=CREATE_NO_WINDOW)
    else:
        proc.kill()
    proc.wait()


def read_jsonl(path):
    """한 줄에 JSON 하나인 날 출력 → 객체 목록. `{` 로 안 여는 줄과 못 푸는 줄은 건너뛰고, 파일이 없으면 빈 목록이다."""
    out = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line.startswith('{'):
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def footer_line(footer, fields, status, cells):
    """끝 줄 — `<footer> <갈래>` 뒤에 칸을 `fields`(이름, 뜻)의 차례로 ` · ` 로 잇는다. `cells` 는 {칸 이름: 꼴을 갖춘 글}이고 있는
    칸만 든다. 이름이 `fields` 에 없으면 KeyError — 칸을 더하면서 뜻을 안 다는 일을 막는다."""
    unknown = set(cells) - {name for name, _ in fields}
    if unknown:
        raise KeyError(f'끝 줄 칸의 표에 없는 칸: {sorted(unknown)}')
    return ' · '.join([f'{footer} {status}'] + [cells[name] for name, _ in fields if name in cells])


def exit_table(exit_codes, words):
    """종료 코드 표의 줄들 — `exit_codes` 에서 같은 코드를 쓰는 이름끼리 묶고 `words` 로 뜻을 단다. 이름은 끝 줄의 갈래다."""
    names = {}
    for name, code in exit_codes.items():
        names.setdefault(code, []).append(name)
    joined = {code: ' · '.join(ns) for code, ns in names.items()}
    width = max(len(j) for j in joined.values())
    return [f'  {code}  {joined[code]:<{width}}  ' + ' · '.join(words.get(n, n) for n in names[code])
            for code in sorted(names)]


def show_help(ap, epilog, ok):
    """`--help` — 도움말을 표준 출력에 찍고 `ok`(종료 코드)를 낸다. 인자 검사보다 앞서고 파일은 안 쓴다."""
    ap.epilog = epilog
    out = sys.stdout
    if out is None:   # pythonw 에는 표준 출력이 없다 — 찍을 곳이 없다
        return ok
    if hasattr(out, 'reconfigure'):   # 윈도 파이프의 기본 인코딩(cp949)은 `—` 를 못 적어 죽는다 — 에이전트 셸은 UTF-8 로 읽는다
        out.reconfigure(encoding='utf-8')
    out.write(ap.format_help())
    return ok


def main(build_parser, help_epilog, run, footer, exit_codes):
    """러너 한 판 — 인자를 가르고 `run(a)` 의 종료 코드를 낸다. `--help` 는 인자 검사보다 앞선다. 인자가 틀렸거나 `run` 이
    멈추면 그 까닭을 `--out` 파일의 끝 줄(`<footer> usage · …` · `<footer> failed · …`)로 남긴다 — 부른 쪽은 그것만 본다."""
    ap = build_parser()
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        return show_help(ap, help_epilog(), exit_codes['ok'])
    try:
        a = ap.parse_args(args)
    except Usage as e:
        out = out_arg(args)
        if out:
            try:
                write(out, f'{footer} usage · 인자가 틀렸다 — {e}\n')
            except OSError:
                pass
        return exit_codes['usage']
    try:
        return run(a)
    except Exception as e:   # 어디서 멈췄든 답 파일과 끝 줄을 남긴다
        write(a.out, f'{traceback.format_exc()}\n{footer} failed · 러너가 멈췄다 — {type(e).__name__}: {e}\n')
        return exit_codes['failed']
