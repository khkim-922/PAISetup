---
name: norm-remote-truth
description: "원격 · 브랜치 · 커밋의 상태를 판정하려 할 때 부른다 — 「main 이 뒤처졌다」 · 「처음 생긴 커밋」 · 「밀 것이 있다」. 규범 [Main is the Default] 의 ⚠ 본문. origin/* 와 로컬 main 은 마지막 fetch 의 사진이다."
user-invocable: false
---

# 원격이 어디에 있나는 원격에 물어 판정한다

⚠ `origin/*` 와 로컬 main 은 마지막으로 성공한 fetch 때의 사진이라 세션 도중 조용히 낡고, 얕은 클론은 이력의 처음이 잘려 있다 — 그
사진으로 「main 이 뒤처졌다」 · 「처음 생긴 커밋」을 판정하면 헛일을 민다.
