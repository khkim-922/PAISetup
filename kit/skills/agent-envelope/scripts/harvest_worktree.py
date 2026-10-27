"""레인 작업 트리 거두기 — 레인이 손댄 파일을 본 사본에 복사하고, 본 사본도 그 사이 바꾼 파일은 손에 남긴다.

    python harvest_worktree.py <트리> [--into <본 사본>] [--merge] [--dry-run] [--remove [--force]]

차례
  1. 트리의 출발점(본 사본 HEAD 와의 공통 조상)을 잡고, 레인이 손댄 파일을 센다 — 커밋 안 한 것과 출발점 뒤에 커밋한 것
  2. 본 사본이 그 사이 바꾼 파일을 센다 — 출발점 뒤의 커밋과 지금 작업 사본의 변경
  3. 본 사본과 레인이 이미 같은 파일은 「같다」로 두고(앞서 거둔 것), 겹치지 않는 파일은 바이트 그대로 복사하고(레인이 지운 것은
     지운다) 해시로 같음을 본다. 겹친 파일은 손대지 않고 양쪽을 볼 명령을 댄다 — 어떻게 얹나는 사람의 판단이다.
     `--merge` 면 겹친 파일 가운데 양쪽이 고치기만 한 것을 파일마다 3-way 로 얹는다(`git merge-file` — 출발점 판이 바탕). 충돌이
     난 파일은 표식을 남긴 채 손에 남긴다. 본 사본에 커밋 안 한 변경이 있는 파일과 더하기 · 지우기가 엇갈린 파일은 안 얹는다
  4. 복사한 글 파일에서 충돌 표식(`<<<<<<<` 로 열리고 `=======` · `>>>>>>>` 가 따르는 것)을 찾는다
  5. `--remove` 면 겹침 · 어긋남 · 표식이 없을 때만 트리와 그 브랜치를 걷는다. 겹친 파일을 손으로 얹은 뒤에는 `--force` 를 같이
     준다 — 얹었는지는 기계가 못 가른다. 잠긴 트리(레인이 도는 중)는 `--force` 로도 안 걷고 말한다
종료 — 0 다 거뒀다 · 1 손에 남은 것이 있다(겹침 · 해시 어긋남 · 충돌 표식 · 잠긴 트리) · 2 못 쟀다(트리가 아니다 · git 이 졌다)
  · 4 부르는 법이 틀렸다

복사이지 패치가 아닌 까닭 — 작업 사본의 줄끝이 색인과 다른 설정에서는 트리에서 뽑은 diff 가 본 사본에 안 붙고, 붙어도 줄끝을
바꿔 쓴다. 바이트 복사는 레인이 쓴 그대로를 옮기고, 본 사본의 커밋이 훅을 그대로 탄다. 본 사본의 작업 사본 변경도 「그 사이
바뀐 것」으로 세는 까닭 — 커밋 안 한 변경을 덮으면 되돌릴 데가 없다. 겹친 파일을 레인 브랜치에 임시 커밋을 만들어 옮기지
않고 `--merge` 로 파일마다 합치는 까닭 — 임시 커밋은 커밋 훅(메시지 형식 · 게이트)을 우회하게 만들고, 파일 합치기는 커밋 없이
같은 3-way 를 낸다. 게이트는 본 사본의 커밋에서 돈다.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARK_OPEN, MARK_MID, MARK_CLOSE = '<<<<<<< ', '=======', '>>>>>>> '
TEXT_SCAN_MAX = 4 * 1024 * 1024   # 충돌 표식을 찾을 글 파일의 크기 한도 — 그보다 크면 안 본다고 말한다
HARNESS_TREES = '.claude/worktrees/'   # 하네스가 트리를 세우는 자리 — 본 사본의 변경을 셀 때 뺀다(다른 레인의 트리다)
NUL = chr(0)


class GitFailed(Exception):
    pass


# 커밋 훅이 자식에게 물려주는 저장소 변수 — 남겨 두면 `git -C <자리>` 가 그 자리가 아니라 훅을 돌린 저장소를 고친다.
# 이름은 git 이 댄다(`git rev-parse --local-env-vars`). git 이 못 대면 이 목록으로 걷는다.
HOOK_VARS = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
             'GIT_COMMON_DIR', 'GIT_PREFIX', 'GIT_IMPLICIT_WORK_TREE', 'GIT_CONFIG_PARAMETERS', 'GIT_NAMESPACE')


def clean_env():
    env = dict(os.environ)
    try:
        names = subprocess.run(['git', 'rev-parse', '--local-env-vars'], capture_output=True, text=True, timeout=20).stdout.split()
    except (OSError, subprocess.SubprocessError):
        names = []
    for k in set(names) | set(HOOK_VARS):
        env.pop(k, None)
    return env


ENV = clean_env()


def git(cwd, *args):
    p = subprocess.run(['git', '-c', 'core.quotePath=false', '-C', str(cwd), *args], capture_output=True, env=ENV)
    if p.returncode != 0:
        raise GitFailed(f'git {" ".join(args)} → {p.returncode}: {p.stderr.decode("utf-8", "replace").strip()}')
    return p.stdout.decode('utf-8', 'replace')


def git_bytes(cwd, *args):
    """git 의 답을 바이트 그대로 — 파일 내용(`show <판>:<경로>`)을 줄끝째 옮길 때."""
    p = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, env=ENV)
    if p.returncode != 0:
        raise GitFailed(f'git {" ".join(args)} → {p.returncode}: {p.stderr.decode("utf-8", "replace").strip()}')
    return p.stdout


def merge_one(main, base, path, src, dst):
    """겹친 파일 하나를 3-way 로 얹는다 — 바탕은 출발점 판. 충돌 수를 낸다(0 이면 깨끗하다). 안 얹었으면 그 까닭(글)을 낸다."""
    if subprocess.run(['git', '-C', str(main), 'diff', '--quiet', 'HEAD', '--', path], env=ENV).returncode != 0:
        return '본 사본에 커밋 안 한 변경이 있다 — 합치다 틀리면 되돌릴 데가 없다'
    with tempfile.TemporaryDirectory() as d:
        b = Path(d) / 'base'
        b.write_bytes(git_bytes(main, 'show', f'{base}:{path}'))
        p = subprocess.run(['git', 'merge-file', '-L', 'main', '-L', f'base {base[:7]}', '-L', 'lane', str(dst), str(b), str(src)],
                           capture_output=True, env=ENV)
    if p.returncode < 0:
        return f'git merge-file 이 졌다 — {p.stderr.decode("utf-8", "replace").strip()}'
    return p.returncode


def zsplit(out):
    return [s for s in out.split(NUL) if s]


def worktree_changes(repo):
    """작업 사본의 변경 — {경로: 'A' | 'M' | 'D'}. 이름을 바꾼 것은 옛 자리 D · 새 자리 A. 추적 안 하는 폴더는 `경로/` 로 온다."""
    items = zsplit(git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all'))
    out, i = {}, 0
    while i < len(items):
        xy, path = items[i][:2], items[i][3:]
        i += 1
        if xy[0] in 'RC':          # -z 꼴은 새 경로 다음 항목이 옛 경로다
            old = items[i]
            i += 1
            if xy[0] == 'R':
                out[old] = 'D'
            out[path] = 'A'
            continue
        if xy == '??' or 'A' in xy:
            out[path] = 'A'
        elif 'D' in xy:
            out[path] = 'D'
        else:
            out[path] = 'M'
    return out


def committed_changes(repo, base, head):
    """출발점 뒤에 커밋한 변경 — 꼴은 worktree_changes 와 같다."""
    items = zsplit(git(repo, 'diff', '--name-status', '-z', base, head))
    out, i = {}, 0
    while i < len(items):
        st = items[i][0]
        if st in 'RC':
            old, new = items[i + 1], items[i + 2]
            i += 3
            if st == 'R':
                out[old] = 'D'
            out[new] = 'A'
            continue
        out[items[i + 1]] = 'D' if st == 'D' else ('A' if st == 'A' else 'M')
        i += 2
    return out


def main_checkout_of(tree):
    """이 트리가 매인 본 사본 — worktree 목록의 첫 항목."""
    first = git(tree, 'worktree', 'list', '--porcelain').splitlines()[0]
    return Path(first[len('worktree '):])


def worktree_entry(main, tree):
    """본 사본의 worktree 목록에서 이 트리의 항목(줄들) — 없으면 None."""
    want = os.path.normcase(os.path.realpath(tree))
    for block in git(main, 'worktree', 'list', '--porcelain').strip().split('\n\n'):
        lines = block.splitlines()
        if lines and lines[0].startswith('worktree ') and os.path.normcase(os.path.realpath(lines[0][9:])) == want:
            return lines
    return None


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def marker_lines(path):
    """충돌 표식이 선 줄 번호들 — `<<<<<<<` 로 여는 줄이 없으면 빈 목록(`=======` 홀로는 제목 밑줄일 수 있다). 글이 아니거나 크면 None."""
    if path.stat().st_size > TEXT_SCAN_MAX:
        return None
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except (UnicodeDecodeError, OSError):
        return None
    if not any(line.startswith(MARK_OPEN) for line in lines):
        return []
    return [n for n, line in enumerate(lines, 1) if line.startswith((MARK_OPEN, MARK_CLOSE)) or line == MARK_MID]


def moved_in_main(main, base, head):
    """본 사본이 출발점 뒤에 바꾼 것 — (파일 집합, 추적 안 하는 폴더 접두사들)."""
    files = set(zsplit(git(main, 'diff', '--name-only', '-z', base, head)))
    dirs = []
    for path in worktree_changes(main):
        if path.startswith(HARNESS_TREES):
            continue
        if path.endswith('/'):
            dirs.append(path)
        else:
            files.add(path)
    return files, dirs


def run(a):
    tree = Path(a.tree).resolve()
    try:
        top = Path(git(tree, 'rev-parse', '--show-toplevel').strip()).resolve()
    except GitFailed as e:
        print(f'✗ 트리가 아니다 — {e}')
        return 2
    if os.path.normcase(str(top)) != os.path.normcase(str(tree)):
        print(f'✗ 저장소 뿌리가 아니다 — {tree} (뿌리는 {top})')
        return 2
    main = Path(a.into).resolve() if a.into else main_checkout_of(tree).resolve()
    if os.path.normcase(str(main)) == os.path.normcase(str(tree)):
        print('✗ 본 사본과 트리가 같다 — 거둘 것이 없다')
        return 2
    # 아무것도 만지기 전의 울타리 — 트리가 본 사본의 worktree 목록에 서 있어야 그 본 사본이다. 아니면 본 사본을 잘못 가린 것이라
    # (훅이 물려준 변수 · 다른 저장소의 트리) 복사가 엉뚱한 저장소를 고친다
    if worktree_entry(main, tree) is None:
        print(f'✗ 본 사본 {main} 의 worktree 목록에 이 트리가 없다 — 거두지 않는다. 본 사본이 맞으면 --into 로 대고, 다른 저장소의 트리면 이 스크립트의 일이 아니다')
        return 2
    tree_head = git(tree, 'rev-parse', 'HEAD').strip()
    main_head = git(main, 'rev-parse', 'HEAD').strip()
    base = git(main, 'merge-base', main_head, tree_head).strip()
    try:
        branch = git(tree, 'symbolic-ref', '--short', 'HEAD').strip()
    except GitFailed:
        branch = None
    ahead = git(main, 'rev-list', '--count', f'{base}..{main_head}').strip()

    lane = committed_changes(tree, base, tree_head)
    lane.update(worktree_changes(tree))
    moved, moved_dirs = moved_in_main(main, base, main_head)

    print(f'트리 {tree}' + (f' · 브랜치 {branch}' if branch else ' · 떼어 낸 HEAD') + f' · 출발점 {base[:7]} · 본 사본 {main} HEAD {main_head[:7]}'
          + (f' (출발점에서 {ahead} 커밋 앞)' if ahead != '0' else ''))
    tag = '(dry-run) ' if a.dry_run else ''
    pending, overlaps, copied = [], [], []
    if not lane:
        print('레인이 손댄 파일이 없다')
    for path in sorted(lane):
        kind, src, dst = lane[path], tree / path, main / path
        # 이미 거둔 것 — 본 사본과 레인이 같으면 할 일이 없다(두 번째 부름 · 손으로 얹은 뒤의 --remove)
        if kind == 'D' and not dst.exists():
            print(f'같다  {path} (이미 없다)')
            continue
        if kind != 'D' and src.is_file() and dst.is_file() and sha(src) == sha(dst):
            print(f'같다  {path} (이미 거뒀다)')
            continue
        if path in moved or any(path.startswith(d) for d in moved_dirs):
            print(f'겹침  {path} — 본 사본도 그 사이 바꿨다. 레인 판: git -C "{tree}" diff {base[:7]} -- "{path}" · 본 판: git -C "{main}" diff {base[:7]} -- "{path}"')
            overlaps.append(path)
            continue
        if kind == 'D':
            if not a.dry_run:
                dst.unlink()
            print(f'{tag}지움  {path}')
            continue
        if not src.is_file():
            print(f'✗ 못 잼  {path} — 트리에 보통 파일로 없다(서브모듈 · 링크?)')
            pending.append(path)
            continue
        if a.dry_run:
            print(f'{tag}복사  {path}')
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        same = sha(src) == sha(dst)
        print(f'복사  {path}  {"=" if same else "≠ 해시가 다르다"}')
        if not same:
            pending.append(path)
        copied.append((path, dst))
    if a.merge and overlaps:
        for path in list(overlaps):
            src, dst = tree / path, main / path
            if lane[path] != 'M' or path not in moved or not (src.is_file() and dst.is_file()):
                print(f'겹침 그대로  {path} — 양쪽이 고치기만 한 파일만 합친다(더하기 · 지우기가 엇갈렸다)')
                continue
            if a.dry_run:
                print(f'{tag}합침  {path}')
                continue
            got = merge_one(main, base, path, src, dst)
            if isinstance(got, str):
                print(f'겹침 그대로  {path} — {got}')
                continue
            overlaps.remove(path)
            if got:
                print(f'⚠ 합침 · 충돌 {got}  {path} — 표식을 갈라 얹는다')
                pending.append(path)
            else:
                print(f'합침  {path}')
                copied.append((path, dst))
    for path, dst in copied:
        hits = marker_lines(dst)
        if hits is None:
            print(f'· 충돌 표식을 안 봤다  {path} (글이 아니거나 크다)')
        elif hits:
            print(f'⚠ 충돌 표식  {path}:{",".join(map(str, hits))}')
            pending.append(path)

    if a.remove:
        blockers = pending + ([] if a.force else overlaps)
        if a.dry_run:
            print('(dry-run) 걷기는 안 한다')
        elif blockers:
            print(f'걷지 않는다 — 손에 남은 것이 {len(blockers)} 이다' + (' (겹친 파일을 손으로 얹었으면 --force)' if overlaps else ''))
        else:
            if overlaps:
                print(f'겹침 {len(overlaps)} 은 손으로 얹은 것으로 보고 걷는다(--force)')
            entry = worktree_entry(main, tree)
            if entry is None:
                print(f'✗ 본 사본의 worktree 목록에 이 트리가 없다 — 손으로 본다: git -C "{main}" worktree list')
                pending.append('worktree 목록')
            elif any(line.startswith('locked') for line in entry):
                print(f'걷지 않는다 — 트리가 잠겨 있다(레인이 아직 도는가). 끝났으면: git -C "{main}" worktree unlock "{tree}"')
                pending.append('잠긴 트리')
            else:
                git(main, 'worktree', 'remove', '--force', str(tree))
                print(f'걷음  {tree}')
                if branch:
                    in_use = any(line.strip() == f'branch refs/heads/{branch}' for line in git(main, 'worktree', 'list', '--porcelain').splitlines())
                    if in_use:
                        print(f'브랜치 {branch} 는 다른 트리가 쓰고 있어 둔다')
                    else:
                        git(main, 'branch', '-D', branch)
                        print(f'브랜치 {branch} 걷음')
    left = pending + ([] if (a.remove and a.force) else overlaps)
    if left:
        print(f'남은 것 {len(left)} — 겹친 파일은 손으로 얹고, 다 얹으면 --remove --force 로 트리를 걷는다')
        return 1
    if a.dry_run:
        print('dry-run — 아무것도 바꾸지 않았다')
    elif not a.remove:
        print('다 거뒀다 — 트리는 --remove 로 걷는다')
    return 0


def main():
    ap = argparse.ArgumentParser(description='레인 작업 트리의 변경을 본 사본에 복사하고, 본 사본도 그 사이 바꾼 파일은 손에 남긴다')
    ap.add_argument('tree', help='레인의 작업 트리(저장소 뿌리)')
    ap.add_argument('--into', help='본 사본 — 없으면 트리가 매인 본 사본')
    ap.add_argument('--merge', action='store_true', help='겹친 파일 가운데 양쪽이 고치기만 한 것을 파일마다 3-way 로 얹는다(git merge-file)')
    ap.add_argument('--dry-run', action='store_true', help='무엇을 할지만 찍고 아무것도 안 바꾼다')
    ap.add_argument('--remove', action='store_true', help='다 거뒀으면 트리와 그 브랜치를 걷는다')
    ap.add_argument('--force', action='store_true', help='--remove 와 함께 — 겹친 파일을 손으로 얹었으면 겹침이 남아도 걷는다')
    try:
        a = ap.parse_args()
    except SystemExit as e:
        return 0 if e.code == 0 else 4
    try:
        return run(a)
    except GitFailed as e:
        print(f'✗ 못 잼 — {e}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
