// 보고 창에서 누르신 것 — 줄의 「끝났음 · 내일 다시 · 안 올려도 됨」은 메일 번호마다, 「보고 맞추기」의 보고 시각과 「다시 올리기」는 제
// 열쇠로 이 창(file://)의 localStorage 에 남긴다. 일일 보고의 ticks.py 가 로그인 Edge 에서 거두고(시각은 스캔 판이 그 손으로 받는다), 거둔
// 때와 결과를 같은 저장소에 돌려 적는다. 창이 보이는 지금 모습(시각표 · 규칙의 수 · 올리지 않을 것 · 내일 다시 볼 것)은 지을 때의 것
// (`data-state`)과, 그것을 바꾸는 명령 · 스캔 · 거두기가 열린 창에 바로 적는 것(STATE) 가운데 늦은 것이다 — 창은 제가 못 읽는 파일을
// 그 길로만 안다. 메일에서 온 글로 글을 짓지 않는다 — 바꾸는 것은 단추의 눌림 · 숨김, 줄의 class, 이 파일이 든 말, 「HH:MM」 꼴로 거른
// 시각, 받은 글을 글자(textContent)로 옮긴 것, 32자리 메일 번호로만 지은 링크뿐이다. 페이지의 CSP 가 이 글 그대로의 해시만 연다.
(function () {
  "use strict";
  var PREFIX = "$done_prefix", TIMES = "$times_key", UNQUIET = "$unquiet_prefix", STATE = "$state_key";
  var CAL = "$cal_prefix", HAND = "$hand_key", HAND_STALE_MS = $hand_stale_ms;
  var CLOCK = /^([01]\d|2[0-3]):[0-5]\d$$/;          // 끝의 겹친 표지는 window.py 가 채울 때 하나가 된다(string.Template)
  var UNID = /^[0-9A-Fa-f]{32}$$/;
  var FRESH_SCAN_MS = 40 * 60 * 1000;                // 스캔이 이만큼 안에 돌았으면 「다음 스캔에 받는다」고 말한다(기본 15분마다)
  var groups = Array.prototype.slice.call(document.querySelectorAll(".marks[data-unid]"));
  var prefsBox = document.getElementById("prefs");
  var timesBox = document.getElementById("times");
  var quietList = document.getElementById("quiet-list");
  var laterList = document.getElementById("later-list");
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
    if (off && groups.length) off.hidden = false;
    return;
  }
  var prefsOff = document.getElementById("prefs-off");
  if (prefsOff) prefsOff.hidden = true;
  var hint = document.getElementById("prefs-hint");
  if (hint) hint.hidden = false;

  var madeAt = document.querySelector("[data-made]");
  var made = madeAt ? new Date(madeAt.getAttribute("data-made")).getTime() : NaN;

  function parse(key) {
    try {
      var v = JSON.parse(store.getItem(key));
      return v && typeof v === "object" ? v : null;
    } catch (e) {
      return null;
    }
  }

  function time(iso) {
    var t = new Date(iso || "").getTime();
    return isNaN(t) ? NaN : t;
  }

  function two(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function stamp(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return "";
    return (d.getMonth() + 1) + "/" + d.getDate() + " " + two(d.getHours()) + ":" + two(d.getMinutes());
  }

  // ── 지금 모습 ── { times, set, login, room, wait, seen, quiet: [{key, unid, words}], later: [{key, unid, words, due}], at }
  function built() {
    try {
      var s = JSON.parse(prefsBox.getAttribute("data-state") || "null");
      return s && typeof s === "object" ? s : null;
    } catch (e) {
      return null;
    }
  }

  function live() {
    var b = built(), s = parse(STATE);
    var got = s && s.times && (!b || !(time(s.at) < time(b.at))) ? s : b;
    if (!got) return { times: [], set: "", quiet: [], later: [], at: "" };
    got.times = (got.times || []).filter(function (t) { return CLOCK.test(t); });
    got.quiet = got.quiet || [];
    got.later = got.later || [];
    return got;
  }

  function listed(list, unid) {
    return list.some(function (x) { return x.unid === unid; });
  }

  // ── 줄의 단추 ──
  // 표시 — { title, at, mark(done · later · quiet · open · clear), folded(거둔 때) }. 옛 표시는 done(참 · 거짓)만 든다. 이 창을 짓기 전에
  // 거둔 표시는 이 창의 글에 이미 들었다 — 다시 열린 일이 이 창에 할 일로 섰으면 그 일은 지금 열려 있으니, 옛 표시로 단추를 누르지 않는다.
  // 거둔 「내일 다시」 · 「안 올려도 됨」이 그 뒤의 지금 모습에 없으면 대화에서 걷으신 것이다 — 그 표시도 안 쓴다
  function read(unid) {
    var v = parse(PREFIX + unid);
    if (v && v.folded && !isNaN(made) && time(v.folded) < made) return null;
    if (v && v.folded && (v.mark === "later" || v.mark === "quiet")) {
      var s = live();
      if (time(s.at) > time(v.folded) && !listed(v.mark === "later" ? s.later : s.quiet, unid)) return null;
    }
    return v;
  }

  function markOf(v) {
    if (!v) return null;
    if (v.mark) return v.mark;
    return v.done === false ? "open" : "done";
  }

  // 바탕 — 「끝났다고 하신 것」의 줄은 눌린 것, 할 일의 줄은 아무것도 안 눌린 것
  function base(g) {
    return g.getAttribute("data-done") === "1" ? "done" : "none";
  }

  function state(g, v) {
    var m = markOf(v);
    if (!m) return base(g);
    return m === "open" || m === "clear" ? "none" : m;
  }

  function named(g) {
    return "「" + (g.getAttribute("data-title") || "이 일") + "」";
  }

  function fresh(m, g) {
    return { done: "다음 보고부터 올리지 않습니다", later: "내일 첫 보고에 다시 올립니다",
             quiet: named(g) + " 같은 일은 다음 보고부터 올리지 않습니다 — 아래 「올리지 않기로 한 것」에서 되돌립니다",
             open: "다음 보고 때 다시 엽니다", clear: "되돌렸습니다 — 다음 보고부터 다시 올립니다" }[m] || "";
  }

  var FOLDED = { done: "업무 기록에 남았습니다", later: "내일 첫 보고로 미뤘습니다", quiet: "올리지 않기로 배웠습니다", open: "다시 열었습니다",
                 clear: "되돌렸습니다" };

  function paintGroup(g) {
    var v = read(g.getAttribute("data-unid"));
    var now = state(g, v);
    var m = markOf(v);
    Array.prototype.forEach.call(g.querySelectorAll("button[data-mark]"), function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-mark") === now ? "true" : "false");
    });
    var note = g.querySelector(".mark-note");
    if (!v) note.textContent = "";
    else if (v.folded) note.textContent = (FOLDED[m] || "") + " · " + stamp(v.folded);
    else note.textContent = fresh(m, g);
    var row = g.closest("li");
    if (row) {
      row.classList.toggle("is-done", now === "done" && base(g) !== "done");
      row.classList.toggle("is-later", now === "later");
      row.classList.toggle("is-quiet", now === "quiet");
      if (row.id) {                                  // 사람별의 그 일도 같이 — 끝난 일은 지운 꼴로
        Array.prototype.forEach.call(document.querySelectorAll('.people .item[data-anchor="' + row.id + '"]'), function (it) {
          it.classList.toggle("is-done", now === "done" && base(g) !== "done");
        });
      }
    }
    g.hidden = false;
  }

  // 누르면 그 단추로, 눌린 단추를 다시 누르면 바탕으로 — 아직 안 거둔 표시가 바탕으로 돌아오면 지운다(누른 적 없는 것과 같다). 거둔 뒤
  // 바탕으로 돌아오면 그 뜻을 적는다 — 끝났던 일은 다시 연 것(open), 미루거나 올리지 말라던 일은 되돌린 것(clear)이다
  function press(g, k) {
    var unid = g.getAttribute("data-unid");
    var v = read(unid);
    var b = base(g);
    var next;
    if (state(g, v) === k) {
      if (b === "done") next = "open";
      else if (v && v.folded) next = markOf(v) === "done" ? "open" : "clear";
      else next = null;
    } else {
      next = k;
      if (b === "done" && k === "done" && !(v && v.folded)) next = null;
    }
    if (next === null) store.removeItem(PREFIX + unid);
    else store.setItem(PREFIX + unid, JSON.stringify({ title: g.getAttribute("data-title") || "", at: new Date().toISOString(), mark: next }));
  }

  groups.forEach(function (g) {
    Array.prototype.forEach.call(g.querySelectorAll("button[data-mark]"), function (b) {
      b.addEventListener("click", function () {
        try {
          press(g, b.getAttribute("data-mark"));
        } catch (e) {
          g.querySelector(".mark-note").textContent = "표시를 못 남겼습니다 — 대화에서 말씀해 주세요";
          return;
        }
        paintAll();
      });
    });
  });

  // ── 보고 시각 ──
  // 고르신 시각 — { base(그때 보던 시각), times, at, done(스캔이 받은 때), said, refused }. 스캔은 보던 시각에서 더하고 빼신 것만 지금 걸린
  // 시각표 위에 건다. 걸린 때보다 앞서 고른 것은 낡았다 — 나중의 말씀(대화)이 이긴다
  var picked = [];
  var dirty = false;

  function chosen(s) {
    var c = parse(TIMES);
    if (!c) return null;
    if (!c.done && time(c.at) <= time(s.set)) return { stale: true };
    if (c.done && (time(c.done) < time(s.set) || (!isNaN(made) && time(c.done) < made))) return null;
    return c;
  }

  function minutes(t) {
    return parseInt(t.slice(0, 2), 10) * 60 + parseInt(t.slice(3), 10);
  }

  // 더하실 시각을 바로 잰다 — 스캔이 거는 자(`scan_brief.no_room`)와 같은 셈을 시각표에 함께 적힌 수(room · wait)로 한다. 수를 못 받은
  // 창은 재지 않고 비서가 받을 때 잰다고 말한다
  function crowded(times, t, s) {
    if (!s.room || !s.wait) return "";
    var list = times.slice().sort();
    for (var i = 0; i < list.length; i++) {
      var start = minutes(list[i]);
      var next = i + 1 < list.length ? minutes(list[i + 1]) : null;
      var end = Math.min(next === null ? 1440 : next, start + s.wait, 1440);
      if (end - start >= s.room) continue;
      if (list[i] !== t && list[i + 1] !== t) continue;      // 더하시는 시각이 붙은 자리만 — 다른 자리는 스캔이 든다
      var latest = two(Math.floor((1440 - s.room) / 60)) + ":" + two((1440 - s.room) % 60);
      if (next !== null && end === next) {
        return t + " 보고는 " + (list[i] === t ? list[i + 1] : list[i]) + " 보고와 " + (end - start) + "분밖에 안 떨어져 있습니다 — 보고 시각끼리는 " +
               s.room + "분 넘게 띄어 주세요";
      }
      return t + " 보고는 그날이 끝나기까지 " + (end - start) + "분뿐입니다 — 보고 시각은 " + latest + " 전에 두어 주세요";
    }
    return "";
  }

  function chips(s) {
    var add = timesBox.querySelector(".add-time");
    Array.prototype.slice.call(timesBox.querySelectorAll(".chip")).forEach(function (c) { c.parentNode.removeChild(c); });
    picked.forEach(function (t) {
      var chip = document.createElement("span");
      var waiting = s.times.indexOf(t) < 0;
      chip.className = "chip" + (waiting ? " is-new" : "");
      chip.textContent = t;
      if (waiting) {
        var tag = document.createElement("span");
        tag.className = "chip-new";
        tag.textContent = "걸기 전";
        chip.appendChild(tag);
      }
      var x = document.createElement("button");
      x.type = "button";
      x.className = "chip-x";
      x.textContent = "빼기";
      x.setAttribute("aria-label", t + " 빼기");
      x.addEventListener("click", function () { drop(t); });
      chip.appendChild(x);
      timesBox.insertBefore(chip, add);
    });
  }

  function say(text) {
    var said = document.getElementById("times-said");
    if (said) said.textContent = text;
  }

  function diffWords(base, times) {
    var add = times.filter(function (t) { return base.indexOf(t) < 0; });
    var cut = base.filter(function (t) { return times.indexOf(t) < 0; });
    return [add.length ? add.join(" · ") + " 을 더하고" : "", cut.length ? cut.join(" · ") + " 을 빼고" : ""].filter(Boolean).join(" ");
  }

  function paintTimes() {
    var s = live();
    var c = chosen(s);
    if (!dirty) {
      var base = c && !c.stale && !c.done && c.base ? c.base : null;
      picked = s.times.slice();
      if (base) {                                    // 고르신 것을 지금 걸린 것 위에 그대로 다시 얹어 보인다(스캔이 하는 셈과 같다)
        c.times.forEach(function (t) { if (CLOCK.test(t) && picked.indexOf(t) < 0 && base.indexOf(t) < 0) picked.push(t); });
        picked = picked.filter(function (t) { return !(base.indexOf(t) >= 0 && c.times.indexOf(t) < 0); }).sort();
      }
      chips(s);
    }
    var on = s.times.length > 0;                     // 이 창을 지은 뒤 대화에서 보고를 내렸으면 고를 것이 없다
    timesBox.querySelector(".add-time").hidden = !on;
    document.getElementById("times-save").hidden = !on;
    if (!on) {
      say("지금은 사람 없는 보고가 걸려 있지 않습니다 — 대화에서 「보고 시각 걸어 줘」 하시면 겁니다");
      return;
    }
    var now = "지금 걸린 시각은 " + s.times.join(" · ") + " 입니다";
    var alive = Date.now() - time(s.seen) < FRESH_SCAN_MS;
    if (dirty) say("「이대로 바꾸기」를 누르시면 " + (diffWords(s.times, picked) || "그대로") + " 비서가 받아 겁니다. " + now);
    else if (c && c.stale) say("창에서 고르신 뒤에 대화에서 시각을 바꾸셨습니다 — 창에서 고르신 것은 안 걸립니다. " + now);
    else if (c && c.done) say((c.said || "") + " · " + stamp(c.done));
    else if (c && alive) say("고르신 대로 " + (diffWords(c.base || s.times, c.times) || "그대로") + " 비서가 다음 스캔(15분 안팎)에 받아 겁니다. " +
                             "그때까지는 " + s.times.join(" · ") + " 이 걸려 있습니다");
    else if (c) say("고르신 것은 메일함 스캔이 한동안 돌지 않아 아직 안 걸렸습니다 — 스캔이 다시 돌 때까지 안 걸리니 대화에서 「스캔 걸려 있어?」 " +
                    "하고 물어 주세요. " + now);
    else say("");
  }

  function drop(t) {
    if (picked.length < 2) {
      say("시각이 하나는 있어야 합니다 — 사람 없는 보고를 내리시려면 대화에서 말씀해 주세요");
      return;
    }
    picked = picked.filter(function (x) { return x !== t; });
    dirty = true;
    chips(live());
    paintTimes();
  }

  if (timesBox) {
    document.getElementById("time-add").addEventListener("click", function () {
      var input = document.getElementById("time-new");
      var t = (input.value || "").slice(0, 5);
      var s = live();
      if (!CLOCK.test(t)) {
        say("더할 시각을 골라 주세요");
        return;
      }
      if (picked.indexOf(t) >= 0) return;
      var why = crowded(picked.concat([t]), t, s);
      if (why) {
        say(why + ". 더하지 않았습니다");
        return;
      }
      picked.push(t);
      picked.sort();
      input.value = "";
      dirty = true;
      chips(s);
      paintTimes();
      if (!s.room) say("「이대로 바꾸기」를 누르시면 비서가 받을 때 시각끼리의 틈을 재고 겁니다");
    });
    document.getElementById("times-save").addEventListener("click", function () {
      try {
        store.setItem(TIMES, JSON.stringify({ base: live().times, times: picked, at: new Date().toISOString() }));
      } catch (e) {
        say("고르신 시각을 못 남겼습니다 — 대화에서 말씀해 주세요");
        return;
      }
      dirty = false;
      paintTimes();
    });
  }

  // ── 올리지 않기로 한 것 · 내일 다시 볼 것 — 지금 모습에서 세운다 ──
  // 이 창에서 방금 「안 올려도 됨」을 누르신 일은 다음 창을 기다리지 않고 바로 서고, 그 줄의 「다시 올리기」는 줄의 단추를 푸는 것과 같다
  var mailHref = prefsBox ? prefsBox.getAttribute("data-mail-href") || "" : "";

  function linked(span, unid, label) {
    if (!mailHref || !UNID.test(unid || "")) return;
    var a = document.createElement("a");
    a.href = mailHref.replace("UNID", unid.toUpperCase());
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = label;
    span.appendChild(document.createTextNode(" "));
    span.appendChild(a);
  }

  function undoNote(li, v) {
    li.classList.toggle("is-undone", !!v);
    li.querySelector(".undo-note").textContent = !v ? "" : v.folded ? "다시 올리기로 했습니다 · " + stamp(v.folded) : "다음 보고부터 이런 일도 다시 올립니다";
  }

  function rowOf(item, isFresh, g) {
    var li = document.createElement("li");
    li.setAttribute("data-key", item.key);
    if (isFresh) li.className = "is-fresh";
    var words = document.createElement("span");
    words.textContent = item.words;
    linked(words, item.unid, isFresh ? "근거 메일" : "보기 메일");
    li.appendChild(words);
    var b = document.createElement("button");
    b.type = "button";
    b.className = "undo";
    var note = document.createElement("span");
    note.className = "undo-note";
    li.appendChild(b);
    li.appendChild(note);
    if (g) {
      b.textContent = "다시 올리기";
      b.addEventListener("click", function () { press(g, "quiet"); paintAll(); });
    } else {
      var key = UNQUIET + item.key;
      var v = parse(key);
      if (v && v.folded && !isNaN(made) && time(v.folded) < made) v = null;
      b.textContent = v && !v.folded ? "되돌리기 취소" : "다시 올리기";
      b.hidden = !!(v && v.folded);
      undoNote(li, v);
      b.addEventListener("click", function () {
        try {
          if (parse(key)) store.removeItem(key);
          else store.setItem(key, JSON.stringify({ at: new Date().toISOString() }));
        } catch (e) {
          note.textContent = "표시를 못 남겼습니다 — 대화에서 말씀해 주세요";
          return;
        }
        paintAll();
      });
    }
    return li;
  }

  function paintLists() {
    var s = live();
    if (quietList) {
      quietList.textContent = "";
      s.quiet.forEach(function (item) { quietList.appendChild(rowOf(item, false, null)); });
      groups.forEach(function (g) {
        var unid = g.getAttribute("data-unid");
        if (state(g, read(unid)) !== "quiet" || listed(s.quiet, unid)) return;
        quietList.appendChild(rowOf({ key: unid, unid: unid, words: named(g) + " 같은 일 — 이 창에서 방금 「이런 건 안 올려도 됨」 하셨습니다" }, true, g));
      });
      var none = document.getElementById("quiet-none");
      if (none) none.hidden = quietList.children.length > 0;
    }
    if (laterList) {
      laterList.textContent = "";
      s.later.forEach(function (item) {
        var li = document.createElement("li");
        var words = document.createElement("span");
        words.textContent = item.words;
        linked(words, item.unid, "근거 메일");
        li.appendChild(words);
        laterList.appendChild(li);
      });
      var head = document.getElementById("later-head");
      if (head) head.hidden = !s.later.length;
    }
    var asof = document.getElementById("prefs-asof");
    if (asof && s.at) asof.textContent = stamp(s.at) + " 기준입니다 — 대화에서 바꾸시면 메일 비서의 Edge 가 이 창에 바로 알립니다";
    var none2 = document.getElementById("times-none");     // 지을 때 안 걸렸던 창 — 그 뒤 걸렸으면 그렇다고만 말한다(고르는 칸은 다음 창부터)
    if (none2 && s.times.length) none2.textContent = "지금 걸린 보고 시각은 " + s.times.join(" · ") + " 입니다 — 다음 보고 창부터 여기서 고르실 수 있습니다";
  }

  // ── 일정에 넣기 ──
  // 누름 — { at, brief(누른 창의 파일 이름) }. 넣을 값은 거두는 손이 그 창의 보고 글에서 이 열쇠의 카드를 찾아 읽는다 — 창은 열쇠만 남긴다.
  // 거두는 손이 끝을 돌려 적는다 — { …, state, said, done(맺은 때) } · 사내 로그인이 끊겼으면 done 없이 { state: "session", said, tried }.
  // 같은 카드를 또 눌러도 안 들 끝(넣었다 · 이미 있다 · 지났다 · 그 사이 바뀜)과 확인 안 됨은 잠긴다 — 못 넣음만 다시 누르면 새 누름이다.
  // 시작이 지난 카드는 누르기 전부터 잠긴다. 「다시 누르시면 취소」는 누름이 정말 기다리는 때(손이 없다 · 사내 로그인이 끊겼다)에만 말한다 —
  // 손이 살아 있으면 누름은 1초 안에 들어 취소할 틈이 없다
  var puts = Array.prototype.slice.call(document.querySelectorAll("button.put[data-key]"));
  var LOCKED = { added: true, already: true, past: true, unsure: true, moved: true };
  var CANCEL = " · 다시 누르시면 취소";
  var SAID = {
    soon: "곧 넣습니다",
    noHand: "바로 넣는 손이 이 창 곁에 없어 다음 메일함 스캔(15분 안팎)에 넣습니다 — 그 사이 일정이 바뀌면 넣지 않습니다" + CANCEL,
    nobody: "바로 넣는 손도 메일함 스캔도 돌지 않아 아직 못 넣었습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다" + CANCEL,
    past: "지난 약속이라 넣지 않았습니다"
  };

  function pageName() {
    try {
      return decodeURIComponent(location.pathname.split("/").pop() || "");
    } catch (e) {
      return "";
    }
  }

  function startOf(b) {
    return time((b.getAttribute("data-start") || "").replace(" ", "T") + ":00+09:00");   // 카드의 시각은 서울 벽시계다
  }

  function handAlive() {
    var h = parse(HAND);
    return !!h && Date.now() - time(h.beat) < HAND_STALE_MS;
  }

  // 이 창을 짓기 전에 맺은 누름은 이 창의 카드가 아니다 — 같은 판을 다음 보고가 다시 세운 카드(지운 일정)는 처음부터 누를 수 있어야 한다
  function putRecord(b) {
    var v = parse(CAL + b.getAttribute("data-key"));
    if (v && v.done && !isNaN(made) && time(v.done) < made) return null;
    return v;
  }

  function paintPut(b) {
    var v = putRecord(b);
    var note = b.parentNode.querySelector(".put-note");
    var said = "", cls = "", pressed = false, locked = false, label = "일정에 넣기";
    if ((!v || (v.done && !LOCKED[v.state])) && startOf(b) <= Date.now()) {
      said = SAID.past;
      locked = true;
    } else if (v && v.done) {
      said = v.said || "";
      locked = !!LOCKED[v.state];
      pressed = v.state === "added" || v.state === "unsure";
      cls = v.state === "added" ? "ok" : (v.state === "already" || v.state === "past") ? "" : "no";
      if (v.state === "added") label = "넣었습니다";
    } else if (v) {
      pressed = true;
      var age = Date.now() - time(v.at);
      if (v.state === "session") said = (v.said || "") + CANCEL;
      else if (handAlive() || !(age >= HAND_STALE_MS)) said = SAID.soon;
      else if (Date.now() - time(live().seen) < FRESH_SCAN_MS) said = SAID.noHand;
      else said = SAID.nobody;
    }
    b.hidden = false;
    b.textContent = label;
    b.disabled = locked;
    b.setAttribute("aria-pressed", pressed ? "true" : "false");
    if (note) {
      note.textContent = said;
      note.className = "put-note" + (cls ? " " + cls : "");
    }
  }

  // 누르면 그 한 건의 누름을 남기고, 아직 안 거둔 누름을 다시 누르면 지운다(누른 적 없는 것과 같다). 잠긴 끝은 안 바뀐다. 시작이 지난
  // 약속은 남기지 않는다 — 거두는 손도 지난 약속은 안 넣는다(그리면 잠긴다)
  function pressPut(b) {
    var key = CAL + b.getAttribute("data-key");
    var v = putRecord(b);
    if (v && v.done && LOCKED[v.state]) return;
    if (v && !v.done) {
      store.removeItem(key);
      return;
    }
    if (startOf(b) <= Date.now()) return;
    store.setItem(key, JSON.stringify({ at: new Date().toISOString(), brief: pageName() }));
  }

  puts.forEach(function (b) {
    b.addEventListener("click", function () {
      try {
        pressPut(b);
      } catch (e) {
        b.parentNode.querySelector(".put-note").textContent = "누름을 못 남겼습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다";
        return;
      }
      paintPut(b);
    });
  });

  function paintAll() {
    groups.forEach(paintGroup);
    if (timesBox) paintTimes();
    paintLists();
    puts.forEach(paintPut);
  }

  window.addEventListener("storage", paintAll);
  window.addEventListener("focus", paintAll);
  if (puts.length) {                                 // 걸린 누름의 말이 손의 숨 표 · 흐른 때로 바뀐다 — 걸린 누름이 없으면 안 그린다
    window.setInterval(function () {
      if (puts.some(function (b) { var v = putRecord(b); return v && !v.done; })) puts.forEach(paintPut);
    }, 2000);
  }
  paintAll();
})();
