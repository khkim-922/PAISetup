# `_check/` — 배관 검사와 종료코드 계약의 사본

이 폴더의 검사·프로브는 판정을 `_verdict.py` 로 찍고 **종료코드로 말한다.** 어느 검사가 무엇을
재나는 각 파일 머리말과 씨앗 `README.md` 가 든다.

**종료코드 계약과 판정 부품의 진본은 검사 씨앗이다** — `seeds/check/_check/README.md` §종료코드 와
`seeds/check/_check/_verdict.py`. 여기 있는 `_verdict.py` · `exit_code_check.py` 는 그 사본이라 머리말
곁말이 진본을 가리키고 손으로 안 고친다(결정 0040). 사본이 낡았나는 받는 자가 문다:

```bash
python -X utf8 ../check/_check/borrowed_check.py . --seeds ..     # 이 저장소 안에서
python -X utf8 _check/borrowed_check.py                          # 받아 간 저장소에서 — 진본은 ~/.claude/seeds/
```

여기서만 드는 부품은 `_fake_cli.py` 하나다 — 가짜 CLI 를 세우는 자와 **담**. 가짜가 안 서면 진짜
CLI 가 불려 검사가 그날의 구독을 태우므로, 이 폴더에서 어긋남의 값이 제일 큰 파일이다.
