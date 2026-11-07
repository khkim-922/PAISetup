# ECM 손

**회사 PC 의 스크립트 · 스킬이 사내 문서함(ECM)에서 문서를 찾아 읽고, 사람이 확인한 한 편은 편집해 다음 판으로 올리며,
PC 의 파일은 사람이 고른 폴더 · 보안등급으로 새 문서로 올리는 파일들과, 그것을 무는 검사다.**

- **찾는 손** `ecm.py` 의 `Ecm` — 내 문서함과, 그 사람이 볼 수 있는 부서 · 프로젝트 문서함(`cabinets`)의 목록 · 찾기 · 건수. 모든
  요청을 서버에 닿기 전에 잰 꼴에 댄다 — 읽기는 닫힌 목록으로, 바꾸는 요청은 편집 열기와 등록 화면의 두 POST 만 열고, 그 밖(편집취소 ·
  올리기 요청 · 지우기 · 잰 꼴 밖의 서비스와 칸)은 막는다
- **여는 손** `ecm.py` 의 `open_document` — 화면의 「보기」와 같은 두 걸음으로 PC 의 ECM 에이전트를 불러 문서를 받는다. 에이전트는
  받은 파일을 그 확장자의 기본 앱으로 **화면에 띄운다** — 사람이 보는 자리에서만 부른다
- **기본 앱 손** `default_app.py` — 그 확장자의 기본 앱이 안 정해져 있으면 깔린 앱으로 채운다. 이미 고른 값은 안 덮는다
- **읽는 손** `ecm.py` 의 `read_document` — 에이전트가 띄운 그 문서 하나만 닫고(오피스는 `close_view.ps1` · pdf 는 `close_acrobat.ps1`), 받은 파일의 글자를 스킬
  drm-office-read 의 읽는 손으로 뽑는다
- **편집하는 손** `ecm.py` 의 `edit_document` · `checkin_document` — 화면의 「편집」처럼 서버에서 잠가 읽기 쓰기로 열고(체크인이 저장해 올릴 수 있는 워드 · 엑셀 · 파워포인트만 — 그 밖은 잠그기 전에
  멈춘다), 고친 뒤 그
  문서만 저장해 닫아(`close_view.ps1 -Save`) 에이전트의 편집완료 창에서 늘 다음 판과 수정 내용으로 올린다(`checkin_window.ps1`). 바꾸는
  요청은 편집 열기 하나만 짓는다 — 올리기는 에이전트가 한다. 문서를 잠그므로 사람이 그 문서를 확인한 뒤에만 부른다
- **새 문서로 올리는 손** `ecm.py` 의 `register_document` · `folders` — 그 폴더가 그 문서함의 것인가를 폴더 나무로 읽어 본 뒤, 화면의 「컨텐츠 등록」처럼 그 폴더에 같은 이름이 있나 묻고,
  에이전트가 파일을 서버 임시 자리에 올린 뒤 등록하고, 목록에서 다시 읽어 폴더 · 보안등급이 고른 값인가 본다. 같은 이름이 있으면
  안 올린다(다음 판은 편집하는 손의 몫이다). 보안등급 · 공개는 사람이 확인한 값만 받는다 — 잘못 고르면 동료 전체에 보인다
- **얇은 명령** `company_ecm.py` — 대화에서 부르는 명령. 형제 스킬 ep-login 의 `ep_session.py` 로 ECM 세션을 받은 뒤(ECM 만 잰다 — 메일 쪽 Domino 세션은 안 본다) `ecm.py` 를
  그대로 부른다

대화에서 쓰는 절차는 스킬 `company-ecm` 이 든다. 이 폴더는 그 스킬의 명령과, 깔린 자리에서 불러 쓰는 앱이 함께 쓰는 손이다 — 복사해
쓰는 밑판이 아니라 불러 쓰는 손이라, 공개 이름과 꼴(부르는 꼴 · 내는 것 · 종료 값)을 바꾸면 그 쪽이 깨진다. 같은 서비스 모음에
문서를 잠그거나 판을 바꾸는 요청이 섞여 있어 읽기 길은 닫힌 목록으로 들고 편집 열기와 등록은 화면과 같은 차례의 문으로만 연다 — 덮어쓰기 ·
사람 문서 닫기 · 모르는 잠금이 구조상 안 나게. 주소 · 꼴의 사실은 `ecm.py` 머리말 「사내 ECM 에서 잰 것」이, 기본 앱의 사실과 그
출처는 `default_app.py` 머리말이 든다.

## 앱에서 쓰기

1. 세션 — 사내 SSO 를 넘은 Edge 의 쿠키를 Playwright 저장 상태 파일로 받는다. 받는 손과 그 파일의 자리는 스킬 ep-login 이 든다 — 이
   손은 그 자리를 받아 쓰기만 한다(`--session <파일>` · 또는 환경변수 `MAILBOX_COOKIES`). 파일에는 다른 호스트의 쿠키도 들어
   있어도 된다 — ECM 호스트에 맞는 쿠키만 싣는다
2. 부르는 꼴 · 내는 것 · 환경변수 · 종료 값 · 받은 파일이 어떻게 되나는 `ecm.py` 머리말이 든다. 기본 앱의 사실은 `default_app.py`
   머리말이 든다
3. 명령줄로 쓸 때:

   ```bash
   python -X utf8 ecm.py --session <세션 파일> list --search 보고서
   python -X utf8 ecm.py --session <세션 파일> cabinets                       # 부서 · 프로젝트 문서함과 열쇠
   python -X utf8 ecm.py --session <세션 파일> list --cabinet <열쇠> --search 계획
   python -X utf8 ecm.py --session <세션 파일> read <id>
   python -X utf8 ecm.py --session <세션 파일> edit <id>                      # 잠그고 읽기 쓰기로 연다
   python -X utf8 ecm.py --session <세션 파일> checkin <id> <받은 파일> --desc "수정 내용"
   python -X utf8 ecm.py --session <세션 파일> folders <문서함 열쇠> [--parent <폴더 열쇠>]   # 새 문서를 둘 폴더
   python -X utf8 ecm.py --session <세션 파일> register <파일> --cabinet <문서함> --folder <폴더> --security 2A --open F
   python -X utf8 ecm.py default-app .docx      # 기본 앱 상태와 이 PC 의 해시 계산 — 기본 앱이 안 서는 PC 를 들여다볼 때만
   ```

4. 글자를 뽑는 손은 스킬 drm-office-read 의 `read-drm.ps1` 이다 — 다른 자리에 있으면 `ECM_DRM_READER` 로 준다. 윈도 · 오피스 ·
   Fasoo 에이전트가 도는 PC 가 전제다

## 돌려 보기

```bash
python -X utf8 -I check_ecm.py             # 이 폴더의 ecm.py 를 잰다 — 127.0.0.1 밖으로 안 나간다
python -X utf8 -I check_ecm.py --office    # 창 닫는 손까지 — 워드 · 파워포인트 · Acrobat(Reader) 창이 잠깐 뜬다
python -X utf8 -I check_ecm.py <폴더>      # 다른 폴더의 사본을 잰다
```

끝 줄이 「통과 N/N」이면 선 것이다. 가짜 서버 · 가짜 에이전트라 못 재는 길이 있다 — 사내 SSO · 진짜 에이전트 · 편집완료 창 · 서버의
등록 따위, 목록은 `check_ecm.py` 머리말 「여기서 못 재는 것」이 든다.
