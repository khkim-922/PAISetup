# 출처 — 검사 짓기

본문이 기댄 원문과, 우리 판이 원문과 갈린 자리를 든다. 원문은 모두 책 · 논문 · 블로그라 보관본을 두지 않고 인용만
한다. 본문은 이 파일 없이 돈다 — 여기는 사람이 대조하려고 연다.

## 원문

| 원문 | 자리 | 무엇을 가져왔나 |
|---|---|---|
| Humble · Farley, *Continuous Delivery* 5 장 「Anatomy of the Deployment Pipeline」 | https://www.informit.com/articles/article.aspx?p=1621865 (출판사 공개 발췌 · 10 쪽) · https://continuousdelivery.com | 바뀔 때마다 도는 단계 · 앞 단계는 5 분, 길어야 10 분 · 뒤 단계에서 흔히 나는 실패는 앞 단계 시험으로 끌어온다 · 빨강이면 멈추고 고친다 · 단계마다 시작 · 끝을 기록한다 · 믿는 시험 스물이 무시당하는 이천보다 낫다 · 옳은 일을 하기 쉽게 |
| Stewart, 「Test Sizes」(Google Testing Blog, 2010) | https://testing.googleblog.com/2010/12/test-sizes.html | 크기를 이름이 아니라 쓰는 자원(망 · 파일 · 외부)으로 가르고 기계로 지킨다 · 시험은 차례에 안 기댄다 |
| Eagle, 「Change-Detector Tests Considered Harmful」(2015) | https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html | 코드와 같은 정보를 되풀이해 적는 시험은 동작을 못 재면서 고칠 때마다 깨진다 — 값이 마이너스다 · 고치거나 지운다 |
| Vocke, 「The Practical Test Pyramid」(martinfowler.com) | https://martinfowler.com/articles/practical-test-pyramid.html | 보이는 동작을 잰다 · 단계는 종류가 아니라 빠르기 · 범위로 · 시험은 짐이다 · 위층이 잡고 아래층이 못 잡았으면 아래층에 쓴다 · 아래층이 덮고 더하는 값이 없으면 위층을 지운다 · 매몰 비용을 경계 · 끝에서 끝까지 시험은 핵심 흐름만 |
| *Software Engineering at Google* 8 · 11 · 12 · 14 장 | https://abseil.io/resources/swe-book | 규칙은 제 값을 해야 한다(8) · 되는 데까지 도구가 지키고 판단은 사람이(8) · 규칙의 까닭을 적어 다시 보게(8) · 느린 묶음은 덜 돌게 되니 빠르게 고친다(11) · 흔들림이 1 % 에 가까우면 값을 잃는다(11) · 버그를 고치면 빠졌던 사례를 더한다(12) · 무관한 변경에 깨지는 시험은 brittle(12) · 일부러 둔 겹침에도 값이 있다(12) · 큰 시험도 자동으로 · 주인이 없으면 썩는다 · 제출 전 마찰이 크면 제출 뒤 · 릴리스에서(14) |
| Sadowski 외, 「Tricorder」(ICSE 2015) | https://research.google/pubs/tricorder-building-a-program-analysis-ecosystem/ | 새 분석기의 네 조건(이해 쉽고 고칠 길이 뚜렷 · 헛울림 10 % 아래 · 영향 큼 · 드물지만 눈에 띄게 남) · 결과는 체크인 전에, 일하는 흐름 안에서 · 따로 띄우는 도구는 의도보다 덜 쓰인다 · 빌드를 막는 검사는 헛울림이 사실상 0 · 리뷰에서는 바뀐 줄만 · 쓸모없음 10 % 넘으면 지켜보고 25 % 넘으면 끌 수 있다(대개는 고친다) · 버그가 안 고쳐지거나 자원이 크거나 성가시면 끈다 |
| Petrović · Ivanković, 「State of Mutation Testing at Google」(ICSE-SEIP 2018) | https://research.google/pubs/state-of-mutation-testing-at-google/ | 물림은 시험 묶음이 정말 무나를 잰다 · 바뀐 줄만 · 리뷰에서 조언으로 보이고 막지 않는다 |
| 「Future of Google Testing」(ICST 2024 초록) | https://conf.researchr.org/details/icst-2024/cciw-2024-papers/3/Future-of-Google-Testing | 개발 · 제출 전 · 제출 뒤 · 릴리스 네 단계 · 실패할 확률이 높고 싼 결정적 시험은 앞으로 |
| Bhatta · Kendemah · Jha, 「Understanding Test Deletion in Java Applications」(MSR 2025) | https://2025.msrconf.org/details/msr-2025-technical-papers/24/Understanding-Test-Deletion-in-Java-Applications | 실제로 지운 시험 약 2 만 4 천 개의 91 % 가 지키던 코드가 사라진 것 · 「겹친다」로 지운 것의 일부는 커버리지 · 물림 점수를 깎았다 — 서술이지 처방이 아니다 |
| pre-commit 공식 문서 | https://pre-commit.com | 훅은 기본으로 바뀐 파일만 · 전체는 `--all-files` 로 CI 에서 · `manual` 단계 · `fail_fast` 는 기본이 꺼짐 |
| Kent Beck 의 답(Stack Overflow 153234) | Stack Exchange API 로 읽음 | 주어진 확신에 닿는 데 필요한 만큼만 시험한다 · 자주 저지르지 않는 실수는 안 시험한다 — 개인의 방식이다 |

## 본문 절마다 근거

| 절 | 근거 | 한계 |
|---|---|---|
| 1 남길지 | Beck · SWE 8 장 · Tricorder 네 조건 · CD | Beck 은 개인의 방식, Tricorder 는 막지 않는 분석기의 기준이다 — 「조용하다」 · 「다른 자리가 안 잡는다」는 우리가 묶었다 |
| 2 꼴 | SWE 12 장 · Vocke · CD · Change-Detector | 원문은 「사례를 더한다」에서 멈춘다 — 「있는 검사의 한 줄로 · 새 파일은 새 영역만」은 우리가 정했다. 대부분 단위 시험의 글이다 |
| 3 층 | CD 파이프라인 · Google 네 단계 · 물림 논문 | 「결함이 누구에게 닿나」로 가르는 축과 「건넴」은 우리가 정했다 |
| 4 문 | CD 5 장 · Vocke · Google · Tricorder · SWE 14 장 · pre-commit | 원문의 시간은 모두 서버 단계의 값이다 — 만드는 사람 PC 의 문 예산은 없다 |
| 5 판정 | Tricorder · SWE 11 장 · CD | 원문은 둘(통과 · 실패)이다 — 「못 쟀다」는 우리가 더했다 |
| 6 걷기 | Vocke · Tricorder · Change-Detector · MSR 2025 · SWE 12 장 | 「구조상 다시 못 난다」는 원문에 없다 |
| 7 거는 자리 | SWE 8 장 · CD | — |

## 표준과 갈린 자리

| 갈래 | 무엇 | 왜 |
|---|---|---|
| 덮어쓰기 | CD 는 커버리지 같은 지표 문턱으로 커밋 단계를 막으라 한다 — 우리는 지표 문턱을 막는 문에 안 둔다 | SWE 11 장 — 커버리지 목표는 천장이 된다 · 줄이 돌았다는 것이지 맞았다는 것이 아니다 |
| 덮어쓰기 | CD 는 정기 판(밤)을 자동 단계의 반대 꼴로 본다 — 우리는 정기 판을 둔다 | 서버가 없는 자리에서는 바뀔 때마다 도는 뒤 단계가 없다. 정기 판이 그 자리를 메운다 |
| 더하기 | 건넴 · 「결함이 누구에게 닿나」의 층 | 원문은 서버 단계가 있는 한 제품을 전제한다 — 우리는 도구 · 앱 · 문서 저장소가 같이 쓴다 |
| 더하기 | 건넴 절차를 막는 문으로 쓴다 | 원문의 제출 뒤 단계는 서버가 저절로 돌린다 — 서버 없는 저장소는 손으로 건너뛸 수 있는 문만 남는다 |
| 더하기 | 판정 「못 쟀다」 | 원문은 통과 · 실패 둘이다 — 도구가 없거나 자리가 안 맞아 못 잰 것을 통과로 세면 빈 곳이 초록으로 지나간다 |
| 더하기 | 「구조상 다시 못 난다」를 걷는 근거로 | 원문에 없다 — 고쳐서 그 길이 사라진 결함을 재는 검사는 잡을 것이 없다 |
| 더하기 | 혼자 일하는 자리의 「쓸모없음」 신호는 빨강 기록 | Tricorder 는 여럿이 누르는 단추로 잰다 |
| 더하기 | 「크게 다친다」에 허락 없이 일을 끊는 것 · 시간을 크게 빼앗는 것을, 「조용하다」에 보였을 때 되돌릴 수 없는 것을 넣는다 | 원문의 해는 결함 · 데이터 쪽이다. 우리 판정에서 갈렸다(2026-10-15) — 설치기가 허락 없이 앱을 끄면 세션은 이어지지만 그 판의 토큰과 쓰는 사람의 신뢰를 잃고, 깔린 앱을 옛 판으로 다시 까는 일은 잃는 것이 없어도 이미 느린 회사 설치를 두 번 더 돌게 한다 |

## 원문을 다시 읽어 바로잡은 것(2026-10-15)

앞선 요약이 원문을 이렇게 옮겼었다 — 이 판은 바로잡은 쪽을 따른다.

- SWE 11 장의 「느린 묶음은 덜 돌게 된다」를 「느린 것은 덜 돌린다」로 뒤집어 옮겼다 — 원문은 고칠 함정으로 든다
- 물림을 막는 문으로 읽었다 — Google 은 바뀐 줄의 돌연변이를 리뷰의 조언으로 보인다
- 글자 맞춤으로 짓는 물림 장치를 Change-Detector 라 불렀다 — 동작을 재되 구조에 묶인 것이라 SWE 12 장의 brittle 이다(고친다)
- Tricorder 의 25 % 를 「끈다」로 옮겼다 — 「끌 수 있다」이고 대개는 고친다
- pre-commit 이 「느린 것은 pre-push · CI 로」라 한다고 옮겼다 — 공식 문서에 그 말은 없다
- CD 의 커밋 단계를 로컬 훅처럼 읽었다 — 체크인 뒤 서버에서 도는 단계다
- 「걷는 기준은 널리 쓰는 것이 없다」 — 겹침은 Vocke, 성가신 분석기는 Tricorder, 사라진 기능은 MSR 2025 가 다룬다. 없는 것은 「구조상 다시 못 난다」뿐이다

## 못 연 것

- *Continuous Delivery* 7 장(유료) — 5 장 발췌가 커밋 단계를 다 든다
- Stryker · PIT 의 증분 물림 문서 — 「입력이 안 바뀐 결과를 되쓴다」는 확인하지 않았다
