"""Merge the distributed Codex hook example into a user's config.toml."""

import argparse
import pathlib
import re


SPECS = (
    ('UserPromptSubmit', 'drm-guide.py'),
    ('PreToolUse', 'codex-image-gate.py'),
    ('PostToolUse', 'codex-safety-hooks.py'),
)


def assignment(lines, name, start=0, end=None):
    end = len(lines) if end is None else end
    head = re.compile(r'^\s*%s\s*=' % re.escape(name))
    for i in range(start, end):
        if not head.match(lines[i]):
            continue
        depth = 0
        seen = False
        for j in range(i, end):
            depth += lines[j].count('[') - lines[j].count(']')
            seen = seen or '[' in lines[j]
            if seen and depth == 0:
                return i, j + 1
        return None
    return None


def hooks_section(lines):
    for i, line in enumerate(lines):
        if re.match(r'^\s*\[hooks\]\s*$', line):
            for j in range(i + 1, len(lines)):
                if re.match(r'^\s*\[', lines[j]):
                    return i, j
            return i, len(lines)
    return None


def merge(config_text, example_text):
    example = example_text.splitlines()
    blocks = {}
    for name, _ in SPECS:
        span = assignment(example, name)
        if not span:
            raise ValueError('example is missing %s' % name)
        blocks[name] = example[span[0]:span[1]]

    lines = config_text.splitlines()
    while lines and not lines[-1]:
        lines.pop()
    section = hooks_section(lines)
    if section is None:
        if lines:
            lines.append('')
        lines.append('[hooks]')

    changed = False
    skipped = []
    for name, marker in SPECS:
        section = hooks_section(lines)
        start, end = section
        span = assignment(lines, name, start + 1, end)
        block = blocks[name]
        if span is None:
            if end > start + 1 and lines[end - 1]:
                lines.insert(end, '')
                end += 1
            lines[end:end] = block
            changed = True
            continue
        old = lines[span[0]:span[1]]
        if marker not in '\n'.join(old):
            skipped.append(name)
            continue
        if old != block:
            lines[span[0]:span[1]] = block
            changed = True
    return '\n'.join(lines) + '\n', changed, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--example', required=True)
    args = ap.parse_args()
    config = pathlib.Path(args.config).expanduser()
    example = pathlib.Path(args.example)
    try:
        current = config.read_text(encoding='utf-8-sig') if config.exists() else ''
        wanted, changed, skipped = merge(current, example.read_text(encoding='utf-8-sig'))
        if changed:
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(wanted, encoding='utf-8', newline='\n')
        if skipped:
            print('SKIP=' + ','.join(skipped))
        print('CHANGED=' + ('1' if changed else '0'))
        return 0
    except (OSError, ValueError) as exc:
        print('ERROR=' + type(exc).__name__ + ':' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
