// 「끝났음」 표시 — 메일 번호마다 이 창(file://)의 localStorage 에 남기고, 일일 보고의 ticks.py 가 로그인 Edge 에서 거둬 보고 글에 더한다.
// 글을 짓지 않는다 — 바꾸는 것은 상자의 checked · disabled · hidden, 줄의 class, 이 파일이 든 말뿐이다. 메일에서 온 글은 data- 칸에서
// 읽어 저장하기만 한다. 페이지의 CSP 가 이 글 그대로의 해시만 연다 — 한 글자라도 바뀌면 window.py 가 해시를 다시 낸다.
(function () {
  "use strict";
  var PREFIX = "$done_prefix";
  var boxes = Array.prototype.slice.call(document.querySelectorAll("input[data-unid]"));
  if (!boxes.length) return;
  var store = null;
  try {
    if (location.search === "?$via_edge") {
      store = window.localStorage;
      store.getItem(PREFIX);
    }
  } catch (e) {
    store = null;
  }
  if (!store) {
    var off = document.getElementById("tick-off");
    if (off) off.hidden = false;
    return;
  }

  var madeAt = document.querySelector("[data-made]");
  var made = madeAt ? new Date(madeAt.getAttribute("data-made")).getTime() : NaN;

  // 표시 — { title, at, done(없으면 끝났다), folded(보고 글에 거둔 때) }. 이 창을 짓기 전에 거둔 표시는 이 창의 글에 이미 들었다 —
  // 다시 열린 일이 이 창에 할 일로 섰으면 그 일은 지금 열려 있으니, 옛 표시로 상자를 누르지 않는다
  function read(unid) {
    try {
      var v = JSON.parse(store.getItem(PREFIX + unid));
      if (!v || typeof v !== "object") return null;
      if (v.folded && !isNaN(made) && new Date(v.folded).getTime() < made) return null;
      return v;
    } catch (e) {
      return null;
    }
  }

  // 바탕 — 「끝났다고 하신 것」의 줄은 눌린 것, 할 일의 줄은 안 눌린 것
  function base(box) {
    return box.getAttribute("data-done") === "1";
  }

  function two(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function stamp(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return (d.getMonth() + 1) + "/" + d.getDate() + " " + two(d.getHours()) + ":" + two(d.getMinutes());
  }

  function paint() {
    boxes.forEach(function (box) {
      var v = read(box.getAttribute("data-unid"));
      var label = box.parentNode;
      var note = label.querySelector(".tick-note");
      var row = label.closest("li");
      var done = v ? v.done !== false : base(box);
      box.checked = done;
      if (!v) note.textContent = "";
      else if (v.folded) note.textContent = (done ? "업무 기록에 남았습니다 · " : "다시 열었습니다 · ") + stamp(v.folded);
      else note.textContent = done ? "다음 보고부터 올리지 않습니다" : "다음 보고 때 다시 엽니다";
      if (row) row.classList.toggle("is-done", done && !base(box));
      label.hidden = false;
    });
  }

  // 바탕으로 돌아온 아직 안 거둔 표시는 지운다(누른 적 없는 것과 같다). 거둔 뒤 바꾸거나 바탕에서 벗어나면 그 뜻을 적는다 — 거두는 손이
  // 끝났다면 「끝났다고 하신 것」에, 끝나지 않았다면 「안 끝났다고 하신 것」에 옮긴다
  boxes.forEach(function (box) {
    box.addEventListener("change", function () {
      var unid = box.getAttribute("data-unid");
      var v = read(unid);
      try {
        if (!(v && v.folded) && box.checked === base(box)) {
          store.removeItem(PREFIX + unid);
        } else {
          store.setItem(PREFIX + unid, JSON.stringify({ title: box.getAttribute("data-title") || "", at: new Date().toISOString(),
                                                          done: box.checked }));
        }
      } catch (e) {
        box.checked = !box.checked;
        box.parentNode.querySelector(".tick-note").textContent = "표시를 못 남겼습니다 — 대화에서 말씀해 주세요";
        return;
      }
      paint();
    });
  });
  window.addEventListener("storage", paint);
  window.addEventListener("focus", paint);
  paint();
})();
