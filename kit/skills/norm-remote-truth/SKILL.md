---
name: norm-remote-truth
description: "이 순간인가 — origin/* · 로컬 main · 다른 트리의 사본을 읽는 git 명령으로 「원격에 있나 · main 이 뒤처졌나 · 처음 생긴 커밋인가 · 밀 것이 있나」를 답하려 하고, 이 세션에서 내가 fetch 한 뒤가 아니다 → 부른다. 규범 [Main is the Default] 의 ⚠ 본문. 사진은 내 fetch 로만 새로워진다."
user-invocable: false
---

# 원격이 어디에 있나는 원격에 물어 판정한다

⚠ `origin/*` 와 로컬 main 은 마지막으로 성공한 fetch 때의 사진이라 세션 도중 조용히 낡고, 얕은 클론은 이력의 처음이 잘려 있다 — 그
사진으로 「main 이 뒤처졌다」 · 「처음 생긴 커밋」을 판정하면 헛일을 민다.
