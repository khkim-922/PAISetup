# 앞단 HAProxy — 사내 게이트웨이 앞에 선 한 겹

> 사내 게이트웨이(P-GPT) **앞에** 한 겹이 더 있다. 이 문서는 그 층이 무엇이고 **우리
> 트래픽에 무엇을 하는지**를 든다.
>
> ⚠ **전 기능·전 설정 항목은 여기 안 적는다** — 진본은 상류의 공식 설정 매뉴얼이다
> ([`configuration.txt`](https://raw.githubusercontent.com/haproxy/haproxy/master/doc/configuration.txt)
> · 33,073줄 · 버전 3.5 · 2026/08/21). **여기는 그중 우리에게 걸리는 것만** 든다.
> 매뉴얼 자체는 남이 쓴 글이고 1.6 MB 라 **묶음에 안 싣는다** — 가리키는 것으로 족하다.
>
> 게이트웨이 자체의 명세·오류 코드도 여기가 아니다 — `Gemini-Posco.setting.md` ·
> `Claude-Posco.setting.md` · `OpenAI.-Posco.Setting.md` · `errors-Posco.setting.md` 가
> 진본이고, **그 어느 장도 이 층은 안 든다.**

## 어떻게 특정했나 — 오류 몸통이 지문이다

우리가 받은 504 의 몸통이 HAProxy 기본 오류 파일과 **바이트까지 같다.**

```html
<html><body><h1>504 Gateway Time-out</h1>
The server didn't respond in time.
</body></html>
```

## 오류 몸통 대조표 — 어느 층이 냈나

앞단이 제 손으로 만들어 내는 응답들이다. **몸통을 보면 누가 냈는지 갈린다.**

| 코드 | 몸통 | 무슨 일인가 |
|---|---|---|
| 400 | `Your browser sent an invalid request.` | 요청이 깨졌다 |
| 403 | `Request forbidden by administrative rules.` | 규칙이 막았다 |
| 408 | `Your browser didn't send a complete request in time.` | **우리가** 요청을 다 못 보냈다 |
| 500 | `An internal server error occurred.` | 앞단 자신의 오류 |
| 502 | `The server returned an invalid or incomplete response.` | 뒤쪽 응답이 깨졌다 |
| 503 | `No server is available to handle this request.` | 붙을 자리가 없다 |
| **504** | **`The server didn't respond in time.`** | **뒤쪽이 시한 안에 말이 없다 — 우리가 맞은 것** |

**P-GPT 가 낸 것은 다르게 온다** — 코드가 실려 온다(`C055` 「AI 에이전트 응답 시간이
초과되었습니다」). 우리가 받은 것은 코드 없는 맨 HTML 이었다.

⚠ **설정으로 갈아 끼울 수 있다**(`errorfile`). 이 표와 안 맞는다고 HAProxy 가 아닌 것은 아니다.

## 설정이 어떻게 생겼나

| 절 | 무엇을 정하나 |
|---|---|
| `global` | 프로세스 전체 — 로그·최대 연결 수·튜닝 |
| `defaults` | 아래 절들이 물려받는 기본값. **시한을 여기 한 번 적는 것이 관행이다** |
| `frontend` | 받는 쪽 — 무엇을 듣고 어느 `backend` 로 보내나 |
| `backend` | 보내는 쪽 — 서버 목록·부하 분산·헬스체크·**재시도** |
| `listen` | `frontend` + `backend` 를 한 절로 |

## 시한 — 열둘

| 시한 | 무엇을 재나 | 우리에게 |
|---|---|---|
| **`timeout server`** | **서버 쪽 무응답** | **여기서 죽었다** |
| `timeout client` | 클라이언트 쪽 무응답 | 안 걸린다 — 우리는 보내고 기다린다 |
| `timeout connect` | 서버에 붙기까지 | 안 걸린다 |
| `timeout http-request` | 요청을 다 받기까지 | **큰 봉투를 느린 선으로 올리면 408** |
| `timeout queue` | 붙을 자리가 나기까지 | 자리가 없으면 **503** |
| `timeout tunnel` | 업그레이드된 양방향 연결의 유휴 | **SSE 는 업그레이드가 아니라 안 걸린다** (WebSocket 쓰면 그때 본다) |
| `timeout http-keep-alive` | 다음 요청을 기다리는 유휴 | 안 걸린다 |
| `timeout check` · `queue` · `tarpit` · `client-fin` · `server-fin` · `client-hs` | 그 밖 | 안 걸린다 |

## ⚠ 우리를 문 자 — `timeout server`

매뉴얼 원문(§4.2):

> Set the maximum **inactivity** time on the server side.
> The inactivity timeout applies when the server is expected to acknowledge or send data.
> In HTTP mode, this timeout is particularly important to consider **during the first phase
> of the server's response, when it has to send the headers**, as it directly represents
> the server's processing time for the request.

**「무응답 시간」이지 「첫 바이트까지」가 아니다.** 조각이 오면 리셋되고, 스트림 내내
따라다닌다. 그래서 이 제품의 표준 처방이 **심장박동**이다 — 뒤쪽이 할 말이 없을 때도
주기적으로 무언가를 흘려 그 자를 계속 되돌린다.

**기본값이 없다:**

> An unspecified timeout results in an **infinite** timeout, which is not recommended.
> Such a usage is accepted and works but reports a warning during startup.

⚠ 그러니 실측 300초는 **제품 기본값이 아니라 사내에서 정한 값**이다. 통보 없이 바뀔 수 있다.

## 아직 안 물렸지만 물 수 있는 것들

| 무엇 | 어떻게 물 수 있나 |
|---|---|
| **`retries` · `option redispatch`** | **요청이 두 번 나갈 수 있다.** 매뉴얼이 「By default, retries apply only to new connection attempts」라 **지금은 안전하다** — 붙기 전 실패만 되보낸다. 다만 `retry-on` 을 켜 두면 **이미 보낸 요청도 되보낸다.** 우리에게 그건 **LLM 호출 두 번 = 토큰 두 배**고 화면에는 안 보인다. 사내가 켰는지 우리는 모른다. ⚠ **앱의 「다시 안 부른다」는 이 층까지 못 간다** — 끊긴 바퀴를 되부르지 않는 것은 우리 층의 보장이고(atelier `_check/cut_resume_check.py` 가 그것을 잰다), 여기서 되보내는 것은 그 자 밖이다 |
| `maxconn` · `timeout queue` | 붐비면 **503**. 위 대조표로 갈린다 |
| `option http-no-delay` | 낮은 지연을 성능보다 우선한다. 안 켜면 작은 조각이 뭉쳐 나갈 수 있다 — 스트리밍 체감에 걸린다 |
| `errorfile` | 위 대조표를 무력화한다 |
| 압축·헤더 재작성·ACL | 봉투를 손댈 수 있다. 안 겪었지만 못 겪는다는 뜻은 아니다 |

## 되보내기가 켜지면 — 우리에게 무엇이 무나

**「켜든 끄든 아무 일 없게」는 못 만든다.** 기전이 통째로 저쪽에 있고, 매뉴얼이 주는
처방(**고유 거래 ID**)은 **서버가 그 열쇠를 보고 걸러 줘야** 성립하는데 사내 명세 셋
(`Claude-Posco` · `OpenAI.-Posco` · `Gemini-Posco`)에 그런 열쇠가 없다. 그리고 **두 번
나갔는지 알아챌 수조차 없다** — 답은 하나만 오고, 버려진 쪽의 토큰은 그 응답에 안 실린다.

그런데 **실질적으로는 대부분 막혀 있다.** 막는 자가 셋이고 성질이 다 다르다.

| 무엇이 막나 | 어떻게 |
|---|---|
| **버퍼** | 되보내려면 「copy the whole request into it」이고 「**Requests not fitting in a single buffer will never be retried**」다. `tune.bufsize` 기본이 16KB 인데 우리 봉투는 실측 90~200KB — **큰 문(고치기·렌더)은 애초에 대상이 아니다** |
| **구조** | 답은 우리에게 **하나만** 오고 도구는 게이트웨이가 아니라 앱이 실행한다 — 문서가 두 번 고쳐지지 않는다. 잃는 것은 토큰과 시간뿐이다 |
| **앱의 시한** | `response-timeout` 갈래는 **저쪽 자가 울어야** 발화한다. 앱이 먼저 끊으면 안 운다 — 도구 바퀴가 제 예산으로 끊는 자리가 그것이다 |

⚠ **셋째는 지금 무승부다** — 앱 예산도 앞단 무응답 자도 300초라, 첫 바퀴에서는 어느
쪽이 먼저일지 정해져 있지 않다(둘째 바퀴부터는 앱 쪽이 짧아 늘 먼저다).

⚠ **그렇다고 앱 예산을 이 숫자에 매지 않는다.** 300초는 위에 적었듯 **사내가 정한 값이고
통보 없이 바뀐다** — 「저쪽보다 낮게」로 못 박으면 저쪽이 내려간 날 조용히 뒤집힌다.
정할 근거는 **사람이 얼마나 기다리나**여야 하고, 그 값이 마침 낮으면 이 면역은 덤이다.

**못 막는 것 둘** — `empty-response`(붙었는데 아무것도 안 왔다)는 저쪽 판단이라 손이
없다. 그리고 **먼저 끊는다고 토큰이 안 나가는지는 안 쟀다** — 취소가 뒤쪽까지 전해지는지,
Bedrock 이 거기서 과금을 멈추는지 모른다.

## 우리가 보는 자리 둘

같은 시한인데 **언제 걸리느냐**로 오는 모양이 갈린다.

| | 헤더가 나가기 **전** | 데이터가 흐르는 **중** |
|---|---|---|
| 우리가 받는 것 | **깨끗한 HTTP 504** + 위 몸통 | 끊긴 스트림 (TCP 컷) |
| 까닭 | 헤더가 아직 안 나갔으니 상태 코드를 만들 수 있다 | 이미 200 이 나갔으니 HTTP 오류를 못 만든다 |
| HAProxy 로그 플래그 | `sH` | `sD` |

플래그는 **소문자 첫 글자 = 시한 만료**(대문자면 예기치 못한 끊김), 뒷 글자가 국면이다
(`H` 헤더 · `D` 데이터). ⚠ **우리는 그 로그를 못 본다** — 저쪽 로그를 얻었을 때 읽는
법이지 우리가 잰 것이 아니다.

## 우리가 쥔 손잡이 — 하나뿐이다

**저쪽 설정은 못 고친다.** 시한을 늘려 달라고 하는 길 말고, 우리 쪽에서 되는 것은 하나다.

> **선을 조용하게 두지 않는다.**

무엇이 박동이 되는지는 갈래마다 다르다. 모델이 오래 생각하는 동안 조용해지는 계약이면,
**생각 조각을 흘려 달라고 요청하는 것**이 곧 박동이다 — 시한을 늘리는 것이 아니라
**선을 살려 두는 것**이고, 위에 적은 이 제품의 표준 처방과 같은 길이다.

## ⚠ 180초 컷은 이 층이 아니다

스트림이 **신호 없이** 끊기는 **180초** 자가 따로 있다. **여기가 아니다** — 이 층 실측은
`timeout server` **300초**라 값이 안 맞는다(300 ≠ 180).

**그 자의 진본은 [`ENV-posco.md`](ENV-posco.md)** 다 — P-GPT 층에서 잰 것이라 거기 산다.
여기가 드는 것은 **이 층이 아니라는 사실 하나**뿐이다: 다음 사람이 180초를 앞단에
붙이지 않게.

⚠ 다만 **처방은 같은 자리에 있다** — 위 *「선을 조용하게 두지 않는다」*. 그 판도 조용한
선이 죽은 모양이라, 층이 달라도 무는 자의 성질이 같다.

## 실측값

| 무엇 | 값 |
|---|---|
| `timeout server` | **300초** (301초·300초 두 판) |

## 안 잰 것

- **저쪽 설정도 로그도 못 본다.** 위 값은 전부 클라이언트 쪽에서 역산한 것이다
- **사내가 도는 HAProxy 판을 모른다.** 저장해 둔 매뉴얼은 3.5 인데 저쪽이 더 낮으면
  없는 기능이 섞여 있다 — 항목을 믿기 전에 그 점을 감안한다
- **겹이 더 있을 수 있다.** 확인된 것은 「앞단 HAProxy」와 「P-GPT」 둘이고, 그 사이나
  위에 다른 층이 있는지는 모른다
- **180초 자가 어느 겹인지 모른다.** 앞단이 아니라는 것만 값으로 갈린다(300 ≠ 180) —
  P-GPT 앱인지 그 안의 또 다른 홉인지는 밖에서 못 가른다 ([`ENV-posco.md`](ENV-posco.md))

## 원문이 낡았나 보려면

곁에 원문 사본(`haproxy-configuration.txt`)을 둔 자리에서만 이 대조가 선다 — 묶음에는
안 실리므로, 받은 폴더에는 그 파일이 없다. 그때는 위 링크를 그냥 열어 본다.

```bash
curl -sL https://raw.githubusercontent.com/haproxy/haproxy/master/doc/configuration.txt \
  | diff - haproxy-configuration.txt
```

⚠ **원문은 손대지 않는다.** 우리가 안 것은 이 문서가 들고, 저쪽은 그대로 둔다 — 섞으면
다음에 대조가 안 된다.
