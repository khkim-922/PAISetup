# -*- coding: utf-8 -*-
"""파이썬 API 로 덱을 짓는 최소 예시.

데이터 전체를 JSON 으로 넘기는 길은 `sample_deck.json` 이 든다.

    python build_deck.py sample_deck.json -o sample.pptx

이 파일은 **코드에서 직접 부르는 모양**만 보인다 — 값을 계산해서 넣거나,
테마를 갈아 끼우거나, 슬라이드를 조건부로 넣을 때 쓰는 길이다.

    python example_deck.py out.pptx
"""
import sys

from build_deck import Deck

# 테마는 한 색이 지배하고(dark/primary) 악센트 하나가 붙는다. 주제에 맞게 갈아 끼운다.
FOREST = {
    "dark": "13251B", "dark_panel": "1B3324", "dark_line": "2F5740",
    "primary": "13251B", "secondary": "3F6B4E", "accent": "B8541A",
    "accent_on_dark": "E0A044",
}


def main(out):
    deck = Deck(theme=FOREST)

    cover = deck.add_dark_cover(
        kicker="분기 운영 리뷰  |  2026 Q1",
        title=["숫자가 말하는 것부터", "먼저 본다"],
        subtitle="분기 운영 성과 및 다음 분기 과제",
        lead="지난 분기에 무엇이 움직였고 무엇이 멈췄는지, 그리고 다음 분기에 무엇을 바꿀지 한 줄로 정리한다.",
        quote={"text": "측정하지 않는 것은 관리되지 않는다.", "source": "운영 원칙"},
        stats=[
            {"value": "12", "label": "완료 과제", "desc": "계획 대비 92% 달성"},
            {"value": "3", "label": "지연 과제", "desc": "자원 재배분 검토 대상"},
        ],
        footer={"left": "주관 : 운영기획", "right": "2026. 04"},
    )
    deck.add_notes(cover, "표지에서 방향을 먼저 걸고 들어간다.")

    deck.add_process_gates(
        kicker="실행 관리",
        title="다음 분기 과제는 세 단계로 관리한다",
        steps=[
            {"tag": "1", "title": "선정", "period": "4월",
             "activities": ["과제 심의", "우선순위 확정"],
             "output": "확정 과제 목록", "criteria": "효과 추정 근거 확보"},
            {"tag": "2", "title": "실증", "period": "5~6월",
             "activities": ["현장 적용", "지표 측정"],
             "output": "실증 결과", "criteria": "목표 대비 개선 확인"},
            {"tag": "3", "title": "확산", "period": "7월",
             "activities": ["전 부서 전개", "운영 이관"],
             "output": "운영 매뉴얼", "criteria": "실적 반영"},
        ],
        status_legend={
            "title": "주간 신호등",
            "items": [
                {"level": "ok", "title": "정상", "condition": "계획 대비 90% 이상"},
                {"level": "warn", "title": "주의", "condition": "지연 2주 이내"},
                {"level": "bad", "title": "지연", "condition": "지연 4주 초과"},
            ],
        },
    )

    deck.add_dark_closing(
        kicker="다음 단계",
        title="다음 주까지 결정할 것",
        timeline_steps=[
            {"date": "~4/10", "title": "과제 확정", "desc": "부서별 후보 과제 제출"},
            {"date": "~4/17", "title": "자원 배분", "desc": "인력·예산 배정 확정"},
            {"date": "4월 말", "title": "착수", "desc": "실증 단계 진입"},
        ],
        action_items={
            "title": "부서 협조 요청",
            "items": [
                {"tag": "~4/10", "title": "후보 과제 제출", "desc": "부서당 2건 이상"},
                {"tag": "상시", "title": "지표 원천 공개", "desc": "측정 가능한 데이터 접근 허용"},
            ],
        },
        footer="문의 : 운영기획",
    )

    deck.save(out)
    for w in deck.warnings:
        print("경고: " + w, file=sys.stderr)
    print("%s — 슬라이드 %d장" % (out, len(deck.prs.slides._sldIdLst)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "example.pptx")
