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

여기서만 드는 부품은 둘이다.

- `_fake_cli.py` — 가짜 CLI 를 세우는 자와 **담**. 가짜가 안 서면 진짜 CLI 가 불려 검사가 그날의
  구독을 태우므로, 이 폴더에서 어긋남의 값이 제일 큰 파일이다.
- `_plumb.py` + `gateway.conf` — 검사가 앱의 배관을 무는 자리. 아래 §배관 선언.

## 배관 선언 — `gateway.conf`

검사 다섯(`cli_pipe_check` · `sites_lock_check` · `_fake_cli` · `probe_words_check` ·
`gateway_probe`)은 앱의 배관을 문다. 그런데 **배관이 사는 모듈 이름은 저장소마다 갈린다** — 그
이름을 검사 안에 박으면 다르게 두는 저장소는 사본을 받는 순간 그 줄을 손으로 고쳐야 하고,
고치는 순간 `borrowed_check` 가 어긋남으로 문다. 그래서 **갈리는 것만 검사 밖으로 뺀다**(#26
갈래 1 · 결정 0033 「앱은 갈려도 된다」).

검사는 `from _plumb import gateway, providers` 로 물고, `_plumb.py` 가 이 폴더의
`gateway.conf` 를 읽어 모듈을 고른다. 선언이 없거나 칸이 비면 씨앗 기본값
(`app.gateway` · `app.providers`)으로 돈다 — **배관 이름이 씨앗과 같은 저장소는 선언을 안 채워도
그대로 돈다.**

```ini
[plumb]                                    # 배관이 사는 모듈
module    = app.gateway
providers = app.providers
[where]                                    # `module` 이 **안 드는** 자리만 · `모듈:이름`
LOGS_DIR  = app.config:LOGS_DIR
env_token = app.config:_env_token
[values]                                   # 속성이 **아예 없는** 자리 · 좌표가 아니라 값
ENV_PREFIX = ATELIER
```

**왜 매핑표가 안 되나.** 다섯이 코드로 무는 이름은 스물여덟인데(점으로 스물일곱 · `getattr`
로 하나) **형제 사이에서 갈리는 것은 셋뿐**이다 — `LOGS_DIR` · `ENV_PREFIX` · `env_token`.
나머지 스물넷은 저장소마다 같은 이름으로 산다. 그래서 선언의 몸통은 **모듈 이름 하나**이고
`[where]`·`[values]` 는 예외를 적는 자리로 남는다. 예외가 열을 넘어가기 시작하면 그때는 이
길이 아니라 배관 이름을 맞추는 길이다(#26 갈래 2).

```bash
python -X utf8 _check/_plumb.py --show          # 이 트리의 선언이 무엇으로 풀리나
python -X utf8 _check/_plumb.py --self-check    # 선언이 좌표를 정말 옮기나 — 임시 트리로
```

⚠ **검사 안에 배관 모듈 이름을 다시 적지 않는다.** 적으면 그 검사만 조용히 씨앗 이름에 묶여,
받은 저장소에서 **초록인 채로 남의 모듈을 잰다.** 자식 프로세스로 넘길 때도 `_plumb.MODULE`
을 인자로 건넨다(`sites_lock_check` 가 그 꼴).

⚠ **선언이 「없다」고 한 자리는 「못 쟀다」(2)다 — 빨강이 아니다.** `get`·`slot`·`put` 이
`Missing` 을 던지고 부르는 검사가 그것을 2 로 옮긴다. 안 잰 것이지 어긋난 것이 아니다.
