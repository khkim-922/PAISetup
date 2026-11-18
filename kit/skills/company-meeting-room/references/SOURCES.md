# 출처 — 회의실 예약 스킬

밖의 표준을 빌리지 않았다 — 회의실 예약 앱은 사내 앱이라 공개 스킬 · 명세가 없다. 앱의 자리와 꼴은 앱이 내려 주는 화면 코드(로그인 없이
받는 자바스크립트 묶음)에서 읽고, 회사 PC 에서 실물로 쟀다.

## 회사 PC 에서 잰 것 (2026-11-10)

- 사내 세션(ep-login 의 세션 파일)만으로 SSO 넘김 → 출입증 → 읽기 · 넣기 · 고치기 · 지우기가 다 돈다. 출입증 바꾸기가 한 번 지고
  곧 다시 선 일이 있다 — 손이 한 번 더 받아 본다
- 넣으면 M365 일정 이벤트와 회의실 정책이 켠 Teams 링크가 저절로 생긴다. 참석자에게 가는 회의 안내는 회사 메일로 조금 늦게 온다(쓰는 사람의 말)
- 앱의 미리 검사는 정책(타사 · 승인 · 시간 제한)만 본다 — 겹치는 예약 · 지난 시각은 통과하고, 지난 시각 예약은 넣어진다
- 메일 주소록(company-mail `who`)과 앱의 사람 목록은 같은 사람을 같은 메일 주소로 든다. 앱 목록에는 직책이 없고 동명이인이 많다

## 회사 PC 에서 잰 것 — 시험 예약 한 건 (2026-11-19)

승인 없는 회의실에 참석자 없이 넣고 → 참석자 하나 더하고(`change --add-to`) → 취소했다. 손의 `book` · `change` · `cancel` 이 한
부름씩 섰고 매번 다시 읽어 가렸다.

- 예약 줄에 `updated_at` 이 실린다 — 넣을 때 `created_at` 과 같고, 고치면 바뀐다. 내 예약 · 예약 조회 두 줄 모두에 든다
- 예약 줄에 `teams_meeting` 이 실린다 — `join_url` · `meeting_id` · `meeting_password` · `video_id` · `tenant_key`, 곁에
  `teams_meeting_status: created`. 내 예약 · 예약 조회 두 줄 모두에 든다 — `mine` 이 이것을 `teams` 로 낸다
- `teams_link_visibility` 는 보낸 `private` 그대로 선다
- 승인 없는 회의실은 `status: confirmed` · `approvalState: none` 으로 선다. 넣기 답은 감싸지 않은 예약 그대로였다
- 예약 조회(`reservations?startDate&endDate`)의 줄은 내 예약(`reservations/my`)의 줄과 몸통이 같다(참석자 · Teams · `updated_at`).
  다른 것은 둘 — 내 예약만 `room_names` · `rooms`(회의실 이름 · 자리) · `isOrganizer` · `requiresApproval` 을 싣고, 승인 · 잠금 칸이
  내 예약은 `approvalState` · `lockedRoomIds`, 예약 조회는 `approval_state` · `locked_room_ids` 다. 예약 조회의 회의실 이름은
  `room_ids` 를 회의실 목록에 대어 얻는다. 취소 열쇠가 싣는 칸은 두 줄에서 같다(내 예약 다섯 줄로 견줌) — `day` 의 내 줄이 그 열쇠를 낸다
- 사람 목록(`users/directory`)은 5948 명 · 약 2 MB · 0.3 초다
- 넣은 예약은 회사 일정의 **Teams 일정함**에 제목 앞 「[회의실 예약] 」을 달고 같은 시각으로 저절로 든다(기본 일정함에는 안 든다).
  취소하면 거기서도 사라진다 — 일정 손의 `show` 가 기본으로 Teams 일정함을 읽어 일일 보고가 회의실 회의를 본다

## 회사 PC 에서 잰 것 — 시험 반복 예약 (2026-11-19)

승인 없는 회의실에 참석자 없이 월 · 화 두 업무일의 반복을 넣고 → 전체 제목을 고치고 → 전체를 취소했다. 화면이 「기간 제한 예약」이라
부르는 것이고, 「기간 설정」을 켜고 종료일을 고르면 그날까지 업무일마다 같은 시각에 한 회차씩 선다. 주기(매주 · 격주)를 고르는 칸은 없다.

- 넣기 — 한 건 넣기 몸통에 `is_recurring: true` · `recurring_end_date: YYYY-MM-DD` 를 더해 `POST reservations`. 앱의 미리 검사는 그
  두 칸을 줘도 정책만 본다. 답은 `{reservations: [회차, …]}` 로 감싼다(한 건은 예약 그대로)
- 회차는 예약 한 건씩 따로 서고 `recurring_id`(UUID) 하나로 묶인다. 회차 줄의 `is_recurring` · `recurring_end_date` 는 null 이다.
  Teams 일정함에도 회차마다 한 줄씩 든다
- 반복 전체 고치기 — 회차 하나의 id 로 `PATCH reservations/<id>/series`, 몸통은 한 건 고치기와 같은 꼴에 반복 두 칸을 다시 싣는다.
  답 `{updatedCount, totalRequested, pendingRoomAdditionCount}` · 회차마다 `updated_at` 이 바뀐다
- 반복 전체 취소 — `DELETE reservations/<id>/series`, 답 `{deletedCount, totalRequested}` · 내 예약 · Teams 일정함에서 다 사라진다

## 회사 PC 에서 잰 것 — 내 설정(즐겨찾는 회의실 · 참석자 그룹) (2026-11-19)

시험 즐겨찾기 하나와 시험 그룹 하나(나 혼자)를 넣고 고치고 지웠다 — 끝에 둘 다 비었다. 남에게 가는 알림은 없다.

- 읽기 `GET me/preferences` → `{favorite_rooms: [회의실 id], attendee_groups: [{id, name, members: [{employee_id, email}]}], updated_at, …}`
- 즐겨찾기 하나 넣기 · 빼기 `POST` · `DELETE me/preferences/favorite-rooms/<회의실 id>`, 통째로 갈기 `PUT me/preferences/favorite-rooms
  {room_ids}` — 빈 목록이면 다 빈다
- 그룹 짓기 `POST me/preferences/attendee-groups {name, members}` — 앱이 `id` 를 붙인다. 고치기 `PUT …/attendee-groups/<id> {name,
  members}` · 지우기 `DELETE …/attendee-groups/<id>`
- 바꾸는 요청의 답은 다 바뀐 뒤의 설정 전체이고 `updated_at` 이 바뀐다 — 손은 그 답에서 섰나를 가리고, 열쇠에 `updated_at` 을 싣는다

## 화면 코드가 부르는 사용자 쪽 자리 — 손이 아직 안 부르는 것 (2026-11-19)

앱이 내려 주는 화면 코드(`/scheduler` 의 묶음과 그 조각들)에서 뽑았다. 손가락을 세우기 전에 실물로 한 번 잰다.

- 여러 회의실 묶어 잡기 — 몸통의 `room_ids` 가 여럿을 받는다. 승인이 필요한 회의실이 섞이면 화면이 「회의실 추가 승인 요청됨」을 띄운다
- 대화로 시킬 일이 아니라 안 짓는 것 — 선호 지역 · 공지 팝업 · 사용 설명서(`manuals`) · 앱 안 대화(`agent/…`) · Teams 앱 진입
  (`auth/teams/context`) · 관리(`admin/…` — 승인하기 포함)

## 회사에서 아직 안 잰 것

- 승인이 필요한 회의실에 넣은 예약의 답 꼴(`pending_approval` 로 읽는다) · 앱이 보낸 `confirmed` 를 `pending_approval` 로 바꾸는지
- 고치기에서 회의실을 바꾸는 판 — 회의실 바꾸기는 지었다. `--help` 가 △ 로 보이고 preview 가 알리며, 고친 뒤 다시 읽어 회의실이
  안 바뀌었으면 「확인 못 했다」로 낸다
- 참석자를 바꾼 판에 가는 안내 — 시험에서 더한 참석자가 주관자 자신이라 안내 메일이 안 왔다(몇 분 뒤에도 메일함에 0 통). 남을
  참석자로 둔 판에서 잰다
- 반복의 회차 하나만 고치기 · 취소하기 — 화면이 그 길을 내는지 · 회차 하나에 `PATCH reservations/<id>` 를 부르면 반복에서 떨어지는지
- 반복 전체의 시각 · 회의실 바꾸기, 지난 회차가 든 반복의 전체 고치기 · 취소가 지난 회차까지 건드리는지
- 공휴일에 걸린 회차를 앱이 빼는지 — 화면 코드에 공휴일 이름 목록이 있고 「업무일 전용(주말/공휴일 제외)」이라 적혀 있다. 시험 반복에
  공휴일이 없었다
- `teams_link_visibility` 의 다른 값이 무엇을 가르는지

## 들어가는 길 — `scripts/mrs.py` 가 기댄다

1. 사내 세션 쿠키를 싣고 SSO 넘김 화면(SSO_PAGE)을 GET — 200 에 숨은 칸 폼(ssoToken · domainName · …)이 온다.
   세션이 끊겼으면 그 칸이 없다
2. 그 칸을 폼 꼴(form-urlencoded)로 `api/auth/sso/posco` 에 POST — 302 의 Location 이
   `/auth/sso-callback?accessToken=…&refreshToken=…` 이면 선 것, `/auth/sso-error?code=SSO_VALIDATION_FAILED` 면 진 것.
   JSON 으로 보내면 빈 답이 온다. 같은 세션으로 진 뒤 곧 다시 받으면 서는 일이 있어 한 번 더 받아 본다
3. 그 뒤 `api/<자리>` 를 `Authorization: Bearer <accessToken>` 으로 부른다. 401 은 끊긴 출입증이다

`reservations?startDate&endDate` 는 그 구간에 걸친 예약(여러 달에 걸친 장기 예약 포함)을 다 낸다. 넣으면 M365 일정 이벤트
(`event_id`)와 회의실 정책이 켠 Teams 링크가 저절로 생긴다.
