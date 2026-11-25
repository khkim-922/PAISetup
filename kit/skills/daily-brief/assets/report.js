// 보고 창에서 누르신 것 — 줄의 「끝났음 · 내일 다시 · 안 올려도 됨」은 메일 번호마다, 「보고 맞추기」의 보고 시각 · 자리 밖에서 보기와 「다시 올리기」는 제
// 열쇠로 이 창(file://)의 localStorage 에 남긴다. 일일 보고의 ticks.py 가 로그인 Edge 에서 거두고(시각은 시계 판이 그 손으로 받는다), 거둔
// 때와 결과를 같은 저장소에 돌려 적는다. 창이 보이는 지금 모습(시각표 · 규칙의 수 · 올리지 않을 것 · 내일 다시 볼 것)은 지을 때의 것
// (`data-state`)과, 그것을 바꾸는 명령 · 시계 판 · 거두기가 열린 창에 바로 적는 것(STATE) 가운데 늦은 것이다 — 창은 제가 못 읽는 파일을
// 그 길로만 안다. 메일에서 온 글로 글을 짓지 않는다 — 바꾸는 것은 단추의 눌림 · 숨김, 줄의 class, 이 파일이 든 말, 「HH:MM」 꼴로 거른
// 시각, 받은 글을 글자(textContent)로 옮긴 것, 32자리 메일 번호로만 지은 링크뿐이다. 페이지의 CSP 가 이 글 그대로의 해시만 연다.
// 기능(줄의 단추 · 보고 시각 · 두 목록 · 일정 넣기 · 자리 밖에서 보기 · 부탁 · 결재 창 열기 · 맡길 일)마다 제 함수 범위에 살고, 바탕(열쇠 · 저장소 · 때의 꼴 ·
// 지금 모습)만 함께 쓴다 — 한 기능의 이름이 다른 기능의 이름을 덮지 못한다. 남의 기능은 그 기능이 내놓은 문(Marks · Cal · Ask)으로만 부른다.
(function () {
  "use strict";
  // ── 바탕 — 열쇠 · 저장소 · 때의 꼴 · 지금 모습. 기능마다의 범위가 함께 쓴다 ──
  var PREFIX = "$done_prefix", STATE = "$state_key", HAND = "$hand_key", HAND_STALE_MS = $hand_stale_ms;
  var CLOCK = /^([01]\d|2[0-3]):[0-5]\d$$/;          // 끝의 겹친 표지는 window.py 가 채울 때 하나가 된다(string.Template)
  var UNID = /^$unid_hex$$/;
  var FRESH_CHECK_MS = 40 * 60 * 1000;               // 비서의 확인(시계 판)이 이만큼 안에 돌았으면 「다음 확인에 받는다」고 말한다(기본 15분마다)
  var prefsBox = document.getElementById("prefs");
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
    if (off && (document.querySelector(".marks[data-unid]") || document.querySelector(".todo-row[data-t]"))) {
      off.hidden = false;
      var askOff = document.getElementById("ask-off");   // 「누르신 것을 받지 않는다」 한 줄이 부탁 칸의 까닭까지 든다 — 같은 말을 두 줄 세우지 않는다
      if (askOff) askOff.hidden = true;
    }
    var toBoard = document.querySelector('.toc a[href="#board"]');   // 막대가 안 서는 창 — 그리로 가는 닻도 안 세운다
    if (toBoard) toBoard.parentNode.hidden = true;
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

  // ── 지금 모습 ── { times, set, room, wait, seen, quiet: [{key, unid, words}], later: [{key, unid, words, due}], at }
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
    if (!got) return { times: [], set: "", quiet: [], later: [], away: {}, at: "" };
    got.times = (got.times || []).filter(function (t) { return CLOCK.test(t); });
    got.quiet = got.quiet || [];
    got.later = got.later || [];
    got.away = got.away || {};
    return got;
  }

  function listed(list, unid) {
    return list.some(function (x) { return x.unid === unid; });
  }

  function pageName() {
    try {
      return decodeURIComponent(location.pathname.split("/").pop() || "");
    } catch (e) {
      return "";
    }
  }

  function startOf(el) {
    return time((el.getAttribute("data-start") || "").replace(" ", "T") + ":00$seoul_offset");   // 카드의 시각은 서울 벽시계다
  }

  function handAlive() {
    var h = parse(HAND);
    return !!h && Date.now() - time(h.beat) < HAND_STALE_MS;
  }

  var mailHref = prefsBox ? prefsBox.getAttribute("data-mail-href") || "" : "";

  // ── 줄의 단추 ──
  var Marks = (function () {
    var groups = Array.prototype.slice.call(document.querySelectorAll(".marks[data-unid]"));
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
    function pressMark(g, k) {
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
            pressMark(g, b.getAttribute("data-mark"));
          } catch (e) {
            g.querySelector(".mark-note").textContent = "표시를 못 남겼습니다 — 대화에서 말씀해 주세요";
            return;
          }
          paintAll();
        });
      });
    });

    return { groups: groups, read: read, state: state, named: named, press: pressMark,
             paint: function () { groups.forEach(paintGroup); } };
  })();

  // ── 보고 시각 ──
  var Times = (function () {
    var TIMES = "$times_key";
    var timesBox = document.getElementById("times");
    // 고르신 시각 — { base(그때 보던 시각), times, at, done(받은 때), said, refused }. 시계는 보던 시각에서 더하고 빼신 것만 지금 걸린
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

    // 더하실 시각을 바로 잰다 — 시계가 거는 자(`unattended/brief_slots.first_tight`)와 같은 셈을 시각표에 함께 적힌 수(room · wait)로 한다. 수를 못 받은
    // 창은 재지 않고 비서가 받을 때 잰다고 말한다
    function crowded(times, t, s) {
      if (!s.room || !s.wait) return "";
      var list = times.slice().sort();
      for (var i = 0; i < list.length; i++) {
        var start = minutes(list[i]);
        var next = i + 1 < list.length ? minutes(list[i + 1]) : null;
        var end = Math.min(next === null ? 1440 : next, start + s.wait, 1440);
        if (end - start >= s.room) continue;
        if (list[i] !== t && list[i + 1] !== t) continue;      // 더하시는 시각이 붙은 자리만 — 다른 자리는 시계가 든다
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
        if (base) {                                    // 고르신 것을 지금 걸린 것 위에 그대로 다시 얹어 보인다(시계가 하는 셈과 같다)
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
      var alive = Date.now() - time(s.seen) < FRESH_CHECK_MS;
      if (dirty) say("「이대로 바꾸기」를 누르시면 " + (diffWords(s.times, picked) || "그대로") + " 비서가 받아 겁니다. " + now);
      else if (c && c.stale) say("창에서 고르신 뒤에 대화에서 시각을 바꾸셨습니다 — 창에서 고르신 것은 안 걸립니다. " + now);
      else if (c && c.done) say((c.said || "") + " · " + stamp(c.done));
      else if (c && handAlive()) say("고르신 대로 " + (diffWords(c.base || s.times, c.times) || "그대로") + " 곧 겁니다");
      else if (c && alive) say("고르신 대로 " + (diffWords(c.base || s.times, c.times) || "그대로") + " 비서가 다음 확인(15분 안팎)에 받아 겁니다. " +
                               "그때까지는 " + s.times.join(" · ") + " 이 걸려 있습니다");
      else if (c) say("고르신 것은 비서의 확인이 한동안 돌지 않아 아직 안 걸렸습니다 — 확인이 다시 돌 때까지 안 걸리니 대화에서 「보고 예약 걸려 있어?」 " +
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

    return { on: !!timesBox,
             paint: function () { if (timesBox) paintTimes(); },
             tick: function () { if (timesBox && !dirty && (function (c) { return c && !c.stale && !c.done; })(chosen(live()))) paintTimes(); } };
  })();

  // ── 올리지 않기로 한 것 · 내일 다시 볼 것 — 지금 모습에서 세운다 ──
  var Lists = (function () {
    var UNQUIET = "$unquiet_prefix";
    var quietList = document.getElementById("quiet-list");
    var laterList = document.getElementById("later-list");
    // 이 창에서 방금 「안 올려도 됨」을 누르신 일은 다음 창을 기다리지 않고 바로 서고, 그 줄의 「다시 올리기」는 줄의 단추를 푸는 것과 같다

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
        b.addEventListener("click", function () { Marks.press(g, "quiet"); paintAll(); });
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
      var unread = document.getElementById("prefs-unread");      // 못 읽은 파일이 있으면 비어 보이는 칸이 비어 있는 것이 아니라고 말한다
      if (unread) {
        var names = Array.isArray(s.unread) ? s.unread : [];
        unread.hidden = !names.length;
        unread.textContent = names.length ? names.join(" · ") + "$unread_tail" : "";
      }
      if (quietList) {
        quietList.textContent = "";
        s.quiet.forEach(function (item) { quietList.appendChild(rowOf(item, false, null)); });
        Marks.groups.forEach(function (g) {
          var unid = g.getAttribute("data-unid");
          if (Marks.state(g, Marks.read(unid)) !== "quiet" || listed(s.quiet, unid)) return;
          quietList.appendChild(rowOf({ key: unid, unid: unid, words: Marks.named(g) + " 같은 일 — 이 창에서 방금 「이런 건 안 올려도 됨」 하셨습니다" }, true, g));
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

    return { paint: paintLists };
  })();

  // ── 일정 넣기 ──
  var Cal = (function () {
    var CAL = "$cal_prefix";
    // 누름 — { at, brief(누른 창의 파일 이름) }. 넣을 값은 거두는 손이 그 창의 보고 글에서 이 열쇠의 카드를 찾아 읽는다 — 창은 열쇠만 남긴다.
    // 거두는 손이 끝을 돌려 적는다 — { …, state, said, done(맺은 때) } · 사내 로그인이 끊겼으면 done 없이 { state: "session", said, tried }.
    // 같은 줄을 또 눌러도 안 들 끝(넣었다 · 이미 있다 · 지났다 · 그 사이 바뀜)과 확인 안 됨은 잠긴다 — 못 넣음만 다시 누르면 새 누름이다.
    // 시작이 지난 줄은 누르기 전부터 잠긴다. 「일정 넣기」는 맡길 일의 한 줄로 서고(아래 「맡길 일」), 누르면 차례를 기다리지 않고 이 누름을 남긴다
    var LOCKED = { added: true, already: true, past: true, unsure: true, moved: true };
    var CANCEL = " · 다시 누르시면 취소";
    var SAID = {
      soon: "곧 넣습니다",
      noHand: "바로 넣는 손이 이 창 곁에 없어 비서의 다음 확인(15분 안팎)에 넣습니다 — 그 사이 일정이 바뀌면 넣지 않습니다",
      nobody: "바로 넣는 손도 비서의 확인도 돌지 않아 아직 못 넣었습니다 — 대화에서 「그 약속 넣어 줘」 하시면 넣습니다"
    };

    // 이 창을 짓기 전에 맺은 누름은 이 창의 카드가 아니다 — 같은 판을 다음 보고가 다시 세운 카드(지운 일정)는 처음부터 누를 수 있어야 한다
    function putRecord(b) {
      var v = parse(CAL + b.getAttribute("data-key"));
      if (v && v.done && !isNaN(made) && time(v.done) < made) return null;
      return v;
    }

    // 그 한 건의 누름을 남긴다. 잠긴 끝 · 아직 안 거둔 누름 · 시작이 지난 약속은 안 남긴다 — 거두는 손도 지난 약속은 안 넣는다
    function pressPut(b) {
      var v = putRecord(b);
      if ((v && v.done && LOCKED[v.state]) || (v && !v.done) || startOf(b) <= Date.now()) return;
      store.setItem(CAL + b.getAttribute("data-key"), JSON.stringify({ at: new Date().toISOString(), brief: pageName() }));
    }

    // 아직 안 거둔 그 누름을 지운다 — 누른 적 없는 것과 같다. 누름이 정말 기다리는 때(손이 없다 · 사내 로그인이 끊겼다)에만 단추가 선다
    function cancelPut(b) {
      var v = putRecord(b);
      if (v && !v.done) store.removeItem(CAL + b.getAttribute("data-key"));
    }

    // 「일정 넣기」 줄의 지금 — { st, note, cls, at, cancel }. st: idle · late · wait · done · failed(다시 누른다) · stopped(그 사이 바뀜 — 잠김) · unsure.
    // late 는 그 줄의 「지난 약속」 말(`data-late` — 종류 표가 들고, 넣는 손이 지난 약속을 맺을 때도 같은 말을 적는다)
    function calState(b, late) {
      var v = putRecord(b);
      if ((!v || (v.done && !LOCKED[v.state])) && startOf(b) <= Date.now()) return { st: "late", note: late, cls: "" };
      if (v && v.done) {
        if (v.state === "added" || v.state === "already") return { st: "done", note: v.said || "", cls: v.state === "added" ? "ok" : "", at: v.done };
        if (v.state === "past") return { st: "late", note: v.said || late, cls: "" };
        return { st: v.state === "unsure" ? "unsure" : LOCKED[v.state] ? "stopped" : "failed", note: v.said || "", cls: "no" };
      }
      if (v) {
        var note = SAID.soon, cancel = true;
        if (v.state === "session") note = v.said || "";
        else if (!handAlive() && Date.now() - time(v.at) >= HAND_STALE_MS) note = Date.now() - time(live().seen) < FRESH_CHECK_MS ? SAID.noHand : SAID.nobody;
        else cancel = false;                           // 손이 살아 있으면 누름은 1초 안에 들어 취소할 틈이 없다
        return { st: "wait", note: note + (cancel ? CANCEL : ""), cls: "", cancel: cancel };
      }
      return { st: "idle", note: "", cls: "" };
    }

    return { state: calState, press: pressPut, cancel: cancelPut };
  })();

  // ── 자리 밖에서 보기 ──
  var Away = (function () {
    var AWAY = "$away_key";
    var awayBtn = document.getElementById("away-switch");
    // 고름 — { on, at, done(받은 때), said, refused } · 창 곁의 손이 바로(없으면 시계 판이) 받아 건다. 걸어 둔 고른 때(지금 모습의 away.chosen)보다
    // 앞서 고른 것은 낡았다 — 나중의 말씀(대화)이 이긴다. 이 창을 짓기 전에 받은 고름의 말은 이 창에서 안 쓴다. 받는 분 주소는 지금 모습에서만 온다
    function awayChosen(s) {
      var c = parse(AWAY);
      if (!c || typeof c.on !== "boolean") return null;
      if (time(c.at) < time((s.away || {}).chosen)) return c.done ? null : { stale: true };   // 받은 뒤 대화에서 또 바꾸셨으면 그 말은 지났다
      if (c.done && !isNaN(made) && time(c.done) < made) return null;
      return c;
    }

    function awayPending() {
      var c = awayChosen(live());
      return !!(c && !c.stale && !c.done);
    }

    function paintAway() {
      var s = live(), a = s.away || {}, c = awayChosen(s);
      var pending = !!(c && !c.stale && !c.done);
      var on = pending ? c.on : !!a.on;
      awayBtn.hidden = !s.times.length;                // 이 창을 지은 뒤 대화에서 보고를 내렸으면 고를 것이 없다
      awayBtn.setAttribute("aria-checked", on ? "true" : "false");
      var to = document.getElementById("away-to");
      if (to) to.textContent = a.on && a.address ? "받는 분 — 본인(" + a.address + ") · 바꿀 수 없습니다"
                                                : "지금 꺼져 있습니다 — 받는 분은 본인뿐입니다(켜시면 주소록에서 본인 주소를 받습니다)";
      var said = "", word = on ? "켭니다" : "끕니다";
      if (!s.times.length) said = "지금은 사람 없는 보고가 걸려 있지 않습니다 — 대화에서 「보고 시각 걸어 줘」 하시면 겁니다";
      else if (pending && handAlive()) said = "곧 " + word;
      else if (pending && Date.now() - time(s.seen) < FRESH_CHECK_MS) said = "비서의 다음 확인(15분 안팎)에 " + word + " · 다시 누르시면 취소";
      else if (pending) said = "비서의 확인이 한동안 돌지 않아 아직 안 바뀌었습니다 — 대화에서 「보고 메일로도 보내 줘 · 그만 보내」 하시면 바로 바뀝니다";
      else if (c && c.stale) said = "창에서 고르신 뒤에 대화에서 바꾸셨습니다 — 창에서 고르신 것은 안 따릅니다";
      else if (c && c.done) said = (c.said || "") + " · " + stamp(c.done);
      var note = document.getElementById("away-said");
      if (note) note.textContent = said;
    }

    // 누르면 지금 보이는 것의 반대로 고름을 남기고, 아직 안 받은 고름을 되돌리면(걸린 것과 같아지면) 지운다 — 고른 적 없는 것과 같다
    if (awayBtn) {
      awayBtn.addEventListener("click", function () {
        var s = live(), a = s.away || {}, c = awayChosen(s);
        var pending = !!(c && !c.stale && !c.done);
        var next = !(pending ? c.on : !!a.on);
        try {
          if (pending && next === !!a.on) store.removeItem(AWAY);
          else store.setItem(AWAY, JSON.stringify({ on: next, at: new Date().toISOString() }));
        } catch (e) {
          var note = document.getElementById("away-said");
          if (note) note.textContent = "고르신 것을 못 남겼습니다 — 대화에서 말씀해 주세요";
          return;
        }
        paintAway();
      });
    }

    return { on: !!awayBtn,
             paint: function () { if (awayBtn) paintAway(); },
             tick: function () { if (awayBtn && awayPending()) paintAway(); } };
  })();

  // ── 비서에게 부탁하기 ──
  var Ask = (function () {
    // 부탁 — { words, at, brief(누른 창의 파일 이름), task?(카드의 일 번호), session?(이어 갈 세션) } · 창 곁의 손만 거둔다: 맡으면 taken 을, 다
    // 하면 { state, said, done } 을 적는다. 손이 없으면 남기지 않고 그 자리에서 못 열었다고 말한다 — 시계 판은 부탁을 안 거둔다(자리를 뜬 뒤에
    // VS Code 가 뜨면 놀란다). 누른 지 ASK_TAKE_MS 안에 손이 안 맡으면 못 열었다고 맺어 둔다 — 손도 그보다 늦은 부탁은 안 연다. 맡은 뒤
    // ASK_OPEN_MS 안에 안 끝나면 손이 멈춘 것이다. 칸에 치신 말은 그 말 그대로, 추천 · 카드의 「대화로 열기」 · 「대화로 이어 가기」는 창을
    // 지을 때 그 카드의 근거까지 지어 둔 말(data-*)로 남긴다 — 한 번에 하나다
    var ASK = "$ask_key", ASK_TAKE_MS = $ask_take_ms, ASK_OPEN_MS = $ask_open_ms;
    var ASK_ECHO = 60;                                 // 끝의 말 앞에 다시 보이는 친 말의 글자 수 — 긴 부탁도 끝의 말이 묻히지 않게
    var askBox = document.getElementById("ask");
    var askIn = document.getElementById("ask-in"), askGo = document.getElementById("ask-go");
    var ASK_SAID = {
      opening: "VS Code 를 여는 중입니다…",
      noHand: "대화를 열지 못했습니다 — 이 창을 돕는 비서 프로그램이 멈춰 있습니다. 대화에서 「보고해 줘」 로 보고를 다시 띄우시면 여기서 다시 하실 수 있습니다.",
      // 누를 때는 손이 살아 있었는데 끝내 안 맡았다 — 다른 누름(일정 넣기 따위)을 하느라 늦었을 수도, 그 사이 멈췄을 수도 있다
      noAnswer: "대화를 열지 못했습니다 — 이 창을 돕는 비서 프로그램이 답하지 않았습니다. 다시 눌러 주시고, 그래도 안 되면 대화에서 「보고해 줘」 로 보고를 다시 띄워 주세요.",
      // 손이 맡은 뒤 끝을 안 적었다 — 여는 도중에 멈췄으면 VS Code 가 열렸을 수도 있다. 모르는 것을 「못 열었다」로 말하지 않는다
      unknown: "VS Code 에 열렸는지 확인하지 못했습니다 — 이 창을 돕는 비서 프로그램이 답하지 않았습니다. VS Code 를 보시고 안 열렸으면 다시 눌러 주세요.",
      unsaved: "부탁을 못 남겼습니다 — 대화에서 말씀해 주세요"
    };
    var askHere = null;                                // 이 창에서 방금 못 연 부탁 — 저장소에 안 남긴 것 { words, said, task }
    var askSeen = "";                                  // 끝을 받아 칸을 맞춘 부탁(누른 때) — 그 뒤 새로 치시는 글은 안 건드린다
    var topId = askIn ? askIn.getAttribute("data-top") || "" : "";

    // 이 창에서 누른 부탁만 — 이 창을 짓기 전에 맺은 부탁의 말은 이 창에서 안 쓴다
    function askRecord() {
      var v = parse(ASK);
      if (!v || v.brief !== pageName() || typeof v.words !== "string") return null;
      if (v.done && !isNaN(made) && time(v.done) < made) return null;
      return v;
    }

    function askLate(v) {
      return v.taken ? Date.now() - time(v.taken) >= ASK_OPEN_MS : !(Date.now() - time(v.at) < ASK_TAKE_MS);
    }

    function askWaiting() {
      var v = askRecord();
      return !!v && !v.done && !askLate(v);
    }

    function askLine(words, text, cls) {
      var said = document.getElementById("ask-said");
      said.textContent = "";
      said.className = "ask-said" + (cls ? " " + cls : "");
      if (!text) return;
      var first = words.split("\n")[0];                // 카드의 근거까지 지은 말은 첫 줄(그 일)만 다시 보인다
      var q = document.createElement("q");
      q.textContent = first.length > ASK_ECHO ? first.slice(0, ASK_ECHO) + "…" : first;
      said.appendChild(q);
      said.appendChild(document.createTextNode(" — " + text));
    }

    // 추천 — 칸이 비어 있고 그 일을 아직 안 열었으면 흐린 글 · 「추천」 표 · 그 카드를 대는 설명이 선다. 치시는 순간 사라지고, 비우면 다시 선다
    function topShown() {
      var v = askRecord();
      return !!topId && !askIn.value && !(v && v.task === topId && v.done && v.state === "opened");
    }

    function paintSuggest() {
      if (!topId) return;
      var on = topShown();
      askIn.placeholder = on ? askIn.getAttribute("data-top-line") : askIn.getAttribute("data-plain");
      askIn.classList.toggle("suggest", on);
      var tag = document.getElementById("ask-tag");
      if (tag) tag.hidden = !on;
      document.getElementById("ask-hint").textContent = askIn.getAttribute(on ? "data-top-hint" : "data-hint");
    }

    function paintAsk() {
      var v = askRecord();
      if (v && !v.done && !v.taken && askLate(v)) {    // 손이 끝내 안 맡았다 — 맺어 둔다(늦게 뜬 손이 열지 않게)
        try {
          store.setItem(ASK, JSON.stringify(Object.assign({}, v, { done: new Date().toISOString(), state: "noanswer", said: ASK_SAID.noAnswer })));
        } catch (e) { /* 못 적어도 손이 늦은 부탁은 안 연다 */ }
        v = askRecord();
      }
      var waiting = !!v && !v.done && !askLate(v);
      var hint = document.getElementById("ask-hint");
      askIn.disabled = waiting;
      askGo.disabled = waiting;
      askGo.textContent = waiting ? "여는 중…" : "대화로 열기";
      paintSuggest();
      hint.hidden = waiting || !!askHere || (!!v && !topShown());
      if (waiting) {
        if (!askIn.value && !v.task) askIn.value = v.words;
        askLine(v.words, "", "");
        document.getElementById("ask-said").textContent = ASK_SAID.opening;
        return;
      }
      if (askHere) {
        askLine(askHere.words, askHere.said, "no");
        return;
      }
      if (!v) {
        askLine("", "", "");
        return;
      }
      var opened = v.done && v.state === "opened";
      if (askSeen !== v.at) {                          // 끝을 처음 받았다 — 연 부탁은 칸을 비우고, 못 연 부탁은 다시 누르시게 말을 둔다
        askSeen = v.at;
        askIn.value = opened ? "" : (askIn.value || (v.task ? "" : v.words));
        paintSuggest();
      }
      askLine(v.words, v.done ? (v.said || "") : v.taken ? ASK_SAID.unknown : ASK_SAID.noAnswer, opened ? "ok" : "no");
    }

    // 부탁 하나를 남긴다 — 손이 없거나 못 남기면 그 자리에서 말한다(askHere). 여는 중이면 아무것도 안 한다
    function sendAsk(words, task, session) {
      if (!words || askWaiting()) return;
      askHere = null;
      var rec = { words: words, at: new Date().toISOString(), brief: pageName() };
      if (task) rec.task = task;
      if (session) rec.session = session;
      if (!handAlive()) {
        askHere = { words: words, said: ASK_SAID.noHand, task: task || "" };
      } else {
        try {
          store.setItem(ASK, JSON.stringify(rec));
        } catch (e) {
          askHere = { words: words, said: ASK_SAID.unsaved, task: task || "" };
        }
      }
      paintAll();
    }

    if (askBox) {
      document.getElementById("ask-off").hidden = true;
      askBox.hidden = false;
      askIn.addEventListener("input", paintSuggest);
      askGo.addEventListener("click", function () {
        var words = askIn.value.trim();
        if (!words && topShown()) {
          sendAsk(askIn.getAttribute("data-top-words"), topId, "");
          return;
        }
        if (!words || askWaiting()) {
          askIn.focus();
          return;
        }
        sendAsk(words, "", "");
      });
    }

    return { box: askBox, on: !!askBox, record: askRecord, waiting: askWaiting, send: sendAsk, here: function () { return askHere; },
             paint: function () { if (askBox) paintAsk(); },
             pending: function () { var v = askBox ? askRecord() : null; return !!(v && !v.done); } };
  })();

  // ── 결재 창 열기 ──
  var Appr = (function () {
    // 누름 — APPR<문서 id> 에 { at, brief(누른 창의 파일 이름) }. 창 곁의 손만 거둔다: 맡으면 taken 을, 다 하면 { state(opened · failed · session),
    // said, done } 을 적는다. 손이 없으면 남기지 않고 그 자리에서 대화로 가시라고 말한다 — 시계 판은 안 거둔다(자리를 뜬 뒤에 창이 뜨면 놀란다).
    // 누른 지 ASK_TAKE_MS 안에 손이 안 맡으면 못 띄웠다고 맺는다 — 손도 그보다 늦은 누름은 안 맡는다. 띄운 뒤에도 다시 누르실 수 있다(창을 닫으셨을 때)
    var APPR = "$appr_prefix", TAKE_MS = $ask_take_ms, OPEN_MS = $appr_open_ms;   // 손이 결재 손을 기다리는 시한 + 맡는 틈
    var SAID = {
      opening: "결재 창을 띄우는 중입니다…",
      noHand: "결재 창을 띄우는 비서 프로그램이 이 창 곁에 없습니다 — 대화에서 「그 결재 창 띄워 줘」 하시면 띄웁니다",
      noAnswer: "결재 창을 띄우는 비서 프로그램이 답하지 않았습니다 — 다시 눌러 주시고, 그래도 안 되면 대화에서 말씀해 주세요",
      unknown: "결재 창이 떴는지 확인하지 못했습니다 — 평소 Edge 를 보시고 없으면 다시 눌러 주세요",
      unsaved: "누름을 못 남겼습니다 — 대화에서 「그 결재 창 띄워 줘」 하시면 띄웁니다"
    };
    var buttons = Array.prototype.slice.call(document.querySelectorAll("button.appr-go[data-appr]"));
    var here = {};                                     // 이 창에서 남기지 못한 누름의 말 — 문서 id 마다

    function record(doc) {
      var v = parse(APPR + doc);
      if (!v || v.brief !== pageName()) return null;
      if (v.done && !isNaN(made) && time(v.done) < made) return null;
      return v;
    }

    function late(v) {
      return v.taken ? Date.now() - time(v.taken) >= OPEN_MS : !(Date.now() - time(v.at) < TAKE_MS);
    }

    function paintOne(b) {
      var doc = b.getAttribute("data-appr"), v = record(doc);
      var said = b.parentNode.querySelector(".appr-said");
      var waiting = !!v && !v.done && !late(v);
      b.hidden = false;
      b.disabled = waiting;
      var text = "", cls = "";
      if (here[doc]) { text = here[doc]; cls = "no"; }
      else if (waiting) text = SAID.opening;
      else if (v && v.done) { text = v.said || ""; cls = v.state === "opened" ? "ok" : "no"; }
      else if (v) { text = v.taken ? SAID.unknown : SAID.noAnswer; cls = "no"; }
      said.textContent = text ? " " + text : "";
      said.className = "appr-said" + (cls ? " " + cls : "");
    }

    function press(b) {
      var doc = b.getAttribute("data-appr"), v = record(doc);
      if (v && !v.done && !late(v)) return;
      delete here[doc];
      if (!handAlive()) here[doc] = SAID.noHand;
      else {
        try { store.setItem(APPR + doc, JSON.stringify({ at: new Date().toISOString(), brief: pageName() })); }
        catch (e) { here[doc] = SAID.unsaved; }
      }
      paintAll();
    }

    buttons.forEach(function (b) { b.addEventListener("click", function () { press(b); }); });

    return { on: buttons.length > 0,
             paint: function () { buttons.forEach(paintOne); },
             pending: function () { return buttons.some(function (b) { var v = record(b.getAttribute("data-appr")); return !!(v && !v.done); }); } };
  })();

  // ── 맡길 일 ──
  var Tasks = (function () {
    // 누름 — RUN<창 이름>~<누른 때(ms)> 에 { at, brief, ids(그 차례대로 할 일의 번호), cal(같이 누른 「일정 넣기」 줄의 번호 — 창의 그림만 쓴다),
    // how(batch · card · again) }. 창 곁의 손이 맡으면 taken 을, 하는 동안 TASK<창 이름>/<번호> 에 일마다 { run, state, at, said, items, facts,
    // more, session } 을, 다 하면 누름에 { ended, end, said } 를 적는다. 손이 없으면 누를 때 맺어 두고(end nohand), 누른 지 RUN_TAKE_MS 안에
    // 손이 안 맡으면 창이 맺는다(noanswer) — 손도 그보다 늦은 누름은 안 맡는다. 맡은 뒤 손의 숨 표가 끊기면 창은 맺지 않는다 — 뒤의 실행은
    // 손과 따로 돌아, 창이 아는 것은 연락이 끊겼다는 것뿐이다. 끝을 듣지 못한 일은 「알 수 없음」으로 서고 다시 맡기기를 내지 않는다 — 손이
    // 돌아오면 손이 적는 끝이 선다. 「일정 넣기」 줄은 이 누름에 안 들고 제 누름(위 「일정 넣기」)을 남긴다.
    // 결과의 글은 글자(textContent)로만 세우고, 링크는 32자리 메일 번호에서만 짓는다
    var RUN = "$run_prefix", TASK = "$task_prefix", RUN_TAKE_MS = $run_take_ms, REFUSED = "$run_refused";
    var OPENED = Date.now();                           // 이 창이 선 때 — 다시 연 창은 손이 숨 표를 적을 틈을 준 뒤에야 손과 연락이 끊겼다고 읽는다
    var taskRows = Array.prototype.slice.call(document.querySelectorAll(".todo-row[data-t]"));
    var talkRows = Array.prototype.slice.call(document.querySelectorAll(".todo-row[data-talk]"));
    var boards = Array.prototype.slice.call(document.querySelectorAll(".board"));
    var topBoard = document.getElementById("board");
    var ticked = {};                                   // 표시를 푸신 줄 — 이 창에서만(맡기기 전의 고름이라 남기지 않는다)
    var pressedHere = false;
    var tasksBusy = false;                             // 걸린 누름 · 기다리는 「일정 넣기」가 있나 — 있으면 2초마다 다시 그린다
    var PILL = { wait: ["기다림", ""], doing: ["하는 중", "wait"], done: ["됨", "ok"], asked: ["여쭐 것", "need"], failed: ["못 함", "no"],
                 stopped: ["못 함", "no"], unsure: ["확인 안 됨", "no"], nohand: ["못 맡김", "no"], late: ["지남", ""], lost: ["알 수 없음", "wait"] };
    var W = {
      all: "{n}건", some: "{n}건 가운데 {k}건 표시", go: "표시한 {n}건 맡기기", left: "뺀 {n}건 — {what}",
      running: "하는 중 · {n}건 가운데 {k}건 끝", done: "다 함 · {n}건 · {t}", asked: "여쭐 것 {n}건", nohand: "못 맡김", stopped: "못 끝냄",
      pressed: "맡겼습니다 · {t} — 위에서부터 차례로 합니다. 창을 닫으셔도 계속하고, 다시 여시면 결과가 그대로 서 있습니다.",
      runningSaid: "{t} 에 맡기셨습니다 — 끝난 것은 카드마다 섰습니다. 창을 닫으셔도 계속합니다.",
      reopened: "{t} 에 맡기신 일을 아직 하고 있습니다 — 끝난 것은 카드마다 섰습니다.",
      allDone: "결과는 카드마다 섰습니다.", calWait: "맡기신 일의 결과는 카드마다 섰고, 「일정 넣기」는 아직 기다립니다 — 그 줄에 까닭이 있습니다.", teams: " Teams 회의({c})는 Teams 에서 보내셔야 잡힙니다.",
      askedSaid: "{d}건은 했고, {n}건은 여쭐 것이 있어 멈췄습니다 · {t} — {c}.",
      nohandSaid: "맡기지 못했습니다 — 이 창을 돕는 비서 프로그램이 멈춰 있습니다. 대화에서 「보고해 줘」 로 보고를 다시 띄우시면 여기서 맡기실 수 있습니다.",
      noanswerSaid: "맡기지 못했습니다 — 이 창을 돕는 비서 프로그램이 받지 않았습니다. 다시 맡겨 주시고, 그래도 안 되면 대화에서 「보고해 줘」 로 보고를 다시 띄워 주세요.",
      login: "사내 로그인이 끊겨 {t} 에 멈췄습니다 — {counts}. Edge 에서 메일을 한 번 열어 로그인을 살리신 뒤 다시 맡겨 주세요.",
      lost: "연락 끊김",
      lostSaid: "{t} 에 맡기신 일은 뒤에서 이어지고 있을 수 있습니다 — 이 창을 돕는 비서 프로그램과 연락이 끊겨 어디까지 됐는지 모릅니다. 대화에서 「보고해 줘」 로 보고를 다시 띄우시면 실제로 어떻게 됐는지가 카드마다 섭니다.",
      lostRow: "비서 프로그램과 연락이 끊겨 이 일이 어떻게 됐는지 아직 모릅니다 — 뒤에서 하고 있을 수 있습니다",
      busy: "하는 중", refusedOne: "{c}의 「{kind}」 · {why}", refusedSome: "{n}건을 맡기지 못했습니다 — 까닭은 카드마다 섰습니다.",
      loginHow: " Edge 에서 메일을 한 번 열어 로그인을 살리신 뒤 다시 맡겨 주세요.",
      died: "도중에 멈췄습니다 · {t} — 비서 프로그램이 끝까지 가지 못했습니다. {counts}.",
      partly: "다 마쳤습니다 · {t} — {counts}. 까닭은 카드마다 섰습니다.",
      again: "안 한 {n}건 다시 맡기기",
      noVscode: "이 PC 에는 VS Code 의 Claude Code 가 없어 여기서는 이어 가실 수 없습니다 — 쓰시는 대화 창에서 「그 일 이어서 해 줘」 하고 말씀해 주세요.",
      single: "{c}의 「{kind}」는 따로 맡기셔서 하는 중입니다 — 끝나면 그 카드에 결과가 섭니다.",
      doing: "{t} 에 맡기셨습니다 — 끝나면 여기에 결과가 섭니다",
      failedLogin: "사내 로그인이 끊겨 하지 못했습니다 · {t} — 바뀐 것은 없습니다",
      failedStop: "하지 않았습니다 — 앞의 일 도중에 비서 프로그램이 멈췄습니다. 바뀐 것은 없습니다",
      failedElse: "하지 못했습니다 · {t} — 바뀐 것은 없습니다",
      askedHead: "여쭐 것이 있어 멈췄습니다 · {t}", unsureHead: "도중에 멈춰 됐는지 확인하지 못했습니다 · {t}",
      unsureMore: "「대화로 이어 가기」를 누르시면 비서가 그 일이 됐는지부터 확인합니다 — 다시 맡기시면 같은 일이 두 번 될 수 있습니다.",
      contHint: "VS Code 의 작업 폴더 창에 이 일의 대화가 열립니다 — 여기까지 본 것을 그대로 든 채로요. 그 창은 이 창 뒤에 뜹니다.",
      cont: "대화로 이어 가기", go1: "이것만 맡기기", talk: "대화로 열기", opening: "여는 중…", opened: "열었습니다 · {t}",
      askedWords: "{kind} — {line}\n이 일을 이어서 해 줘. 비서가 멈춘 까닭: {why}", unsureWords: "{kind} — {line}\n이 일을 하다 도중에 멈춰 됐는지 모릅니다 — 됐는지부터 확인해 줘."
    };

    function fmt(t, o) {
      return t.replace(/\{(\w+)\}/g, function (_, k) { return o[k] === undefined ? "" : String(o[k]); });
    }

    function hm(iso) {
      var d = new Date(iso || "");
      return isNaN(d.getTime()) ? "" : two(d.getHours()) + ":" + two(d.getMinutes());
    }

    function cardOf(row, short) {
      var c = row.getAttribute("data-c"), t = row.getAttribute("data-title") || "";
      return c ? (short ? "카드 " + c : "카드 " + c + " 「" + t + "」") : "「" + t + "」";
    }

    // 이 창의 누름 — 누른 차례로. 맺어야 할 누름(늦었다 · 손이 멈췄다)은 여기서 맺는다
    function allRuns() {
      var out = [], page = pageName();
      for (var i = 0; i < store.length; i++) {
        var k = store.key(i);
        if (!k || k.indexOf(RUN) !== 0) continue;
        var v = parse(k);
        if (v && v.brief === page && Array.isArray(v.ids)) out.push({ key: k, id: k.slice(RUN.length), v: v });
      }
      out.sort(function (a, b) { return time(a.v.at) - time(b.v.at); });
      return out.map(function (r) {
        var v = r.v;
        if (v.ended) return r;
        // 맡지 않은 늦은 누름만 맺는다 — 손도 그 누름은 안 맡는다. 맡은 누름의 끝은 손만 적는다(`contactLost`)
        var end = !v.taken && !(Date.now() - time(v.at) < RUN_TAKE_MS) ? "noanswer" : "";
        if (!end) return r;
        r.v = Object.assign({}, v, { ended: new Date().toISOString(), end: end });
        try { store.setItem(r.key, JSON.stringify(r.v)); } catch (e) { /* 못 적어도 그린 것은 같다 */ }
        return r;
      });
    }

    // 맡긴 누름의 손과 연락이 끊겼나 — 손의 숨 표가 끊겼다. 막 연 창은 손이 숨 표를 적을 틈을 준다: 창을 닫은 동안 손은 숨 표를 못 적었을 뿐이다
    function contactLost(v) {
      return !!v.taken && !v.ended && !handAlive() && Date.now() - OPENED >= HAND_STALE_MS;
    }

    function taskRec(id) {
      return parse(TASK + pageName() + "/" + id);
    }

    // 줄 하나의 지금 — { st, rec, run, note, cls, at, cal }. st: idle · late · wait · doing · done · asked · failed · stopped · unsure · nohand
    function rowState(row, runs) {
      var b = row.querySelector("button.put[data-key]");
      if (b) {
        var c = Cal.state(b, row.getAttribute("data-late") || "");
        c.cal = true;
        return c;
      }
      var id = row.getAttribute("data-t"), run = null;
      for (var i = runs.length - 1; i >= 0 && !run; i--) if (runs[i].v.ids.indexOf(id) >= 0) run = runs[i];
      if (!run) {
        if (row.hasAttribute("data-start") && startOf(row) <= Date.now()) return { st: "late", note: row.getAttribute("data-late") || "" };
        return { st: "idle" };
      }
      var rec = taskRec(id);
      if (!rec || rec.run !== run.id) rec = null;
      var s = rec ? rec.state : "", v = run.v;
      if (s === "done" || s === "asked" || s === "failed" || s === "unsure") return { st: s, rec: rec, run: run };
      if (v.ended) {
        if (v.end === "nohand" || v.end === "noanswer") return { st: "nohand", run: run };
        return { st: s === "doing" ? "unsure" : "failed", rec: rec, run: run };
      }
      if (contactLost(v)) return { st: "lost", rec: rec, run: run };
      return { st: s === "doing" ? "doing" : "wait", rec: rec, run: run };
    }

    function el(tag, cls, text) {
      var e = document.createElement(tag);
      if (cls) e.className = cls;
      if (text) e.textContent = text;
      return e;
    }

    function mailLink(label, unid) {
      if (!mailHref || !UNID.test(unid || "")) return document.createTextNode(label || "");
      var a = el("a", "", label || unid.toUpperCase());
      a.href = mailHref.replace("UNID", unid.toUpperCase());
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      return a;
    }

    // 결과의 몸 — said(문단 · 줄바꿈으로 가른다) · items([{label, unid, note}] — 메일 하나에 한 줄) · facts([[이름, 값]]) · more(회색 끝말)
    function resultBody(rec, cls) {
      var body = el("div", cls);
      String(rec.said || "").split("\n").forEach(function (p) { if (p.trim()) body.appendChild(el("p", "", p)); });
      if (Array.isArray(rec.items) && rec.items.length) {
        var ul = el("ul");
        rec.items.forEach(function (it) {
          if (!it || typeof it !== "object") return;
          var li = el("li");
          li.appendChild(mailLink(String(it.label || ""), String(it.unid || "")));
          if (it.note) li.appendChild(document.createTextNode(" — " + it.note));
          ul.appendChild(li);
        });
        body.appendChild(ul);
      }
      if (Array.isArray(rec.facts) && rec.facts.length) {
        var dl = el("dl", "facts");
        rec.facts.forEach(function (f) {
          if (!Array.isArray(f)) return;
          dl.appendChild(el("dt", "", String(f[0] || "")));
          dl.appendChild(el("dd", "", String(f[1] || "")));
        });
        body.appendChild(dl);
      }
      return body;
    }

    // 「대화로 이어 가기」 — 그 일의 줄 · 멈춘 까닭 · 카드의 근거를 채워 대화를 연다. 손이 세션을 적었으면 그 세션을 잇는다
    function contButton(row, x) {
      var id = row.getAttribute("data-t"), v = Ask.record(), mine = v && v.task === id;
      var b = el("button", "btn", W.cont);
      b.type = "button";
      if (mine && !v.done && Ask.waiting()) { b.textContent = W.opening; b.disabled = true; }
      else if (mine && v.done && v.state === "opened") { b.textContent = fmt(W.opened, { t: hm(v.done) }); b.disabled = true; }
      else b.disabled = Ask.waiting();
      b.addEventListener("click", function () {
        var o = { kind: row.getAttribute("data-kind"), line: row.getAttribute("data-line"), why: (x.rec && x.rec.said) || "" };
        var words = fmt(x.st === "asked" ? W.askedWords : W.unsureWords, o) + "\n\n" + (row.getAttribute("data-ev") || "");
        Ask.send(words, id, (x.rec && x.rec.session) || "");
      });
      return b;
    }

    function paintRun(row, box, x) {
      box.textContent = "";
      var head = "", cls = "", st = x.st;
      if (st === "done") {
        head = row.getAttribute("data-head") + " · " + hm(x.rec.at) + (row.getAttribute("data-tail") || "");
        cls = "ok";
      } else if (st === "asked") {
        head = fmt(W.askedHead, { t: hm(x.rec.at) });
        cls = "need";
      } else if (st === "unsure") {
        head = fmt(W.unsureHead, { t: hm((x.rec && x.rec.at) || x.run.v.ended) });
        cls = "no";
      }
      box.hidden = !head;
      if (!head) return;
      box.appendChild(el("p", "run-head " + cls, head));
      if (st === "done") box.appendChild(resultBody(x.rec, "run-body"));
      if (st === "asked") {
        box.appendChild(resultBody({ said: x.rec.said, items: x.rec.items, facts: x.rec.facts }, "run-q"));
        if (x.rec.more) box.appendChild(el("p", "run-more", x.rec.more));
        box.appendChild(el("p", "run-more", Ask.box ? W.contHint : W.noVscode));
      }
      if (st === "done" && x.rec.more) box.appendChild(el("p", "run-more", x.rec.more));
      if (st === "unsure") {
        var r = x.rec || {};
        if ((r.facts && r.facts.length) || (r.items && r.items.length)) box.appendChild(resultBody(r, "run-body"));
        else box.appendChild(el("p", "run-more", r.said || (Ask.box ? W.unsureMore : W.noVscode)));
        if (r.more) box.appendChild(el("p", "run-more", r.more));
      }
      if ((st === "asked" || st === "unsure") && Ask.box) {
        var acts = el("div", "run-actions");
        acts.appendChild(contButton(row, x));
        box.appendChild(acts);
      }
    }

    function rowNote(x) {
      var st = x.st;
      if (x.cal) return st === "idle" ? ["", ""] : [x.note || "", x.cls || ""];
      if (st === "late") return [x.note || "", "no"];
      if (st === "nohand") return [x.run.v.end === "nohand" && !handAlive() ? W.nohandSaid : W.noanswerSaid, "no"];   // 카드 하나를 눌렀어도 까닭이 선다
      if (st === "doing") return [fmt(W.doing, { t: hm(x.run.v.at) }), ""];
      if (st === "lost") return [W.lostRow, ""];
      if (st === "failed") {
        if (x.rec && x.rec.said) return [x.rec.said, "no"];
        var v = x.run.v;
        if (v.end === "session") return [fmt(W.failedLogin, { t: hm(v.ended) }) + (v.how === "card" ? "." + W.loginHow : ""), "no"];   // 따로 맡긴 줄은 막대가 할 일을 안 말한다
        return [v.end === "stopped" ? W.failedStop : fmt(W.failedElse, { t: hm(v.ended) }), "no"];
      }
      return ["", ""];
    }

    // 표시해 맡길 수 있는 줄 — 맡기기 전의 줄과, 따로 맡겼다가 못 맡기거나 못 한 줄(맡긴 판이 없는 때에만 — 판이 서면 「안 한 n건 다시 맡기기」가 든다)
    function rehandable(st) {
      return st === "idle" || st === "failed" || st === "nohand";
    }

    function paintRow(row, x, liveMode) {
      var id = row.getAttribute("data-t"), st = x.st;
      var tickBox = row.querySelector(".todo-tick"), input = tickBox.querySelector("input");
      var go = row.querySelector("button.put"), chip = row.querySelector(".st");
      var note = row.nextElementSibling, box = note.nextElementSibling;
      var canTick = liveMode && (rehandable(st) || st === "late");
      tickBox.hidden = !canTick;
      input.disabled = st === "late";
      input.checked = canTick && rehandable(st) && ticked[id] !== false;
      var showGo = st === "idle" || st === "late" || st === "failed" || st === "nohand" || !!x.cancel;
      go.hidden = !showGo;
      go.disabled = st === "late";
      go.textContent = W.go1;
      go.setAttribute("aria-pressed", x.cancel ? "true" : "false");
      chip.hidden = showGo;
      if (!showGo) {
        chip.textContent = PILL[st][0];
        chip.className = "st" + (PILL[st][1] ? " " + PILL[st][1] : "");
      }
      row.classList.toggle("muted", st === "late" || (canTick && !input.checked));
      var n = rowNote(x);
      note.textContent = n[0];
      note.className = "put-note" + (n[1] ? " " + n[1] : "");
      if (!x.cal) paintRun(row, box, x);
    }

    function paintBrow(li, row, x, liveMode) {
      var st = x.st, id = row.getAttribute("data-t");
      var slot = li.querySelector(".b-tick"), stat = li.querySelector(".b-st");
      var input = slot.querySelector("input");
      var canTick = liveMode && (rehandable(st) || st === "late");
      if (canTick && !input) {
        input = el("input");
        input.type = "checkbox";
        input.setAttribute("data-t", id);
        input.setAttribute("aria-label", row.querySelector(".todo-tick input").getAttribute("aria-label"));
        slot.appendChild(input);
      }
      if (input) {
        input.hidden = !canTick;
        input.disabled = st === "late";
        input.checked = canTick && rehandable(st) && ticked[id] !== false;
      }
      stat.textContent = "";
      if (st !== "idle") {
        var at = x.cal ? x.at : x.rec && x.rec.at;
        stat.appendChild(el("span", "st" + (PILL[st][1] ? " " + PILL[st][1] : ""), PILL[st][0] + (st === "done" && at ? " · " + hm(at) : "")));
      }
      li.classList.toggle("muted", st === "late" || (canTick && !input.checked));
    }

    function counts(c, last) {
      var parts = [[c.done, "건은 했"], [c.unsure, "건은 됐는지 확인하지 못했"], [c.failed, "건은 하지 않았"]].filter(function (p) { return p[0]; });
      return parts.map(function (p, i) {
        var tail = i === parts.length - 1 ? "습니다" : "고";
        return p[0] + p[1] + tail + (p[1].indexOf("확인") >= 0 && c.unsureWhere ? "(" + c.unsureWhere + ")" : "");
      }).join(", ");
    }

    // 맨 나중 판 뒤에 카드에서 따로 맡긴 줄의 지금 — { chip, cls, said } · 없으면 null. 하는 중이면 그 줄들을 대고(판이 없는 창은 표지 없이 —
    // 시안의 「카드에서 하나」), 연락이 끊겼으면 그렇다고, 못 맡겼으면 「못 맡김」과 그 까닭을 댄다 — 그 줄은 다시 맡길 수 있게 남는다
    function singles(infos, batchRuns) {
      var since = batchRuns.length ? time(batchRuns[batchRuns.length - 1].v.at) : -Infinity;
      var mine = infos.filter(function (i) { return !i.x.cal && i.x.run && i.x.run.v.how === "card" && time(i.x.run.v.at) > since; });
      function of(sts) { return mine.filter(function (i) { return sts.indexOf(i.x.st) >= 0; }); }
      var going = of(["wait", "doing"]), lost = of(["lost"]);
      var refused = mine.filter(function (i) {
        var v = i.x.run.v;
        return i.x.st === "nohand" || (i.x.st === "failed" && (v.end === REFUSED || v.end === "session"));
      });
      if (lost.length) return { chip: W.lost, cls: "wait", said: fmt(W.lostSaid, { t: hm(lost[0].x.run.v.at) }) };
      if (going.length) {
        return { chip: batchRuns.length ? W.busy : undefined, cls: "wait",
                 said: going.map(function (i) { return fmt(W.single, { c: cardOf(i.row), kind: i.row.getAttribute("data-kind") }); }).join(" ") };
      }
      if (!refused.length) return null;
      if (refused.length > 1) return { chip: W.nohand, cls: "no", said: fmt(W.refusedSome, { n: refused.length }) };
      var r = refused[0], why = rowNote(r.x)[0];
      return { chip: W.nohand, cls: "no", said: fmt(W.refusedOne, { c: cardOf(r.row), kind: r.row.getAttribute("data-kind"), why: why }) };
    }

    function paintBoards(infos, runs) {
      var batchRuns = runs.filter(function (r) { return r.v.how !== "card"; });
      var liveMode = !batchRuns.length;
      var chipText = "", chipCls = "", said = "", saidCls = "", again = [];
      var goText = "", goOff = true, nText = "", kinds = "", left = "";
      if (liveMode) {
        var pool = infos.filter(function (i) { return rehandable(i.x.st) || i.x.st === "late"; });
        var on = pool.filter(function (i) { return rehandable(i.x.st) && ticked[i.id] !== false; });
        var off = pool.filter(function (i) { return rehandable(i.x.st) && ticked[i.id] === false; });
        var cnt = {}, order = [];
        on.forEach(function (i) { var k = i.row.getAttribute("data-k"); if (!(k in cnt)) { cnt[k] = 0; order.push(k); } cnt[k]++; });
        kinds = order.map(function (k) { return k + " " + cnt[k]; }).join(" · ");
        nText = on.length === pool.length ? fmt(W.all, { n: pool.length }) : fmt(W.some, { n: pool.length, k: on.length });
        goText = fmt(W.go, { n: on.length });
        goOff = !on.length;
        left = off.length ? fmt(W.left, { n: off.length, what: off.map(function (i) { return cardOf(i.row, true) + " 「" + i.row.getAttribute("data-kind") + "」"; }).join(" · ") }) : "";
      } else {
        var inBatch = {};
        batchRuns.forEach(function (r) { r.v.ids.concat(Array.isArray(r.v.cal) ? r.v.cal : []).forEach(function (id) { inBatch[id] = true; }); });
        var B = infos.filter(function (i) { return inBatch[i.id]; }), c = { done: 0, asked: 0, failed: 0, unsure: 0, nohand: 0, busy: 0 };
        var last = batchRuns[batchRuns.length - 1].v, askedRows = [], unsureRows = [], teamsDone = [];
        B.forEach(function (i) {
          var st = i.x.st;
          if (st === "done") c.done++;
          else if (st === "asked") { c.asked++; askedRows.push(i); }
          else if (st === "failed" || st === "stopped") c.failed++;
          else if (st === "unsure") { c.unsure++; unsureRows.push(i); }
          else if (st === "nohand") c.nohand++;
          else if (st === "lost") c.lost = (c.lost || 0) + 1;
          if (!i.x.cal && (st === "wait" || st === "doing")) c.busy++;
          if (i.x.cal && st === "wait") c.calWait = (c.calWait || 0) + 1;
          if (st === "failed") again.push(i);   // 「못 맡김」은 아래에서 따로 — 손이 받을 수 있을 때만 다시 맡긴다
          if (st === "done" && i.row.getAttribute("data-kind") === "$kind_teams") teamsDone.push(cardOf(i.row, true));
        });
        c.unsureWhere = unsureRows.map(function (i) { return cardOf(i.row, true); }).join(" · ");
        var settled = B.filter(function (i) { return i.x.st !== "wait" && i.x.st !== "doing"; }).length;
        var t = hm(last.ended || last.at);
        if (c.lost) {                                  // 손과 연락이 끊겼다 — 끝을 듣지 못한 일이 있는 동안 다시 맡기기를 내지 않는다
          chipText = W.lost; chipCls = "wait";
          said = fmt(W.lostSaid, { t: hm(last.at) });
          again = [];
        } else if (c.busy) {
          chipText = fmt(W.running, { n: B.length, k: settled });
          chipCls = "wait";
          said = pressedHere ? fmt(settled ? W.runningSaid : W.pressed, { t: hm(last.at) }) : fmt(W.reopened, { t: hm(last.at) });
          again = [];
        } else if (last.end === "nohand" || last.end === "noanswer") {
          chipText = W.nohand; chipCls = "no"; saidCls = "no";
          said = last.end === "nohand" && !handAlive() ? W.nohandSaid : W.noanswerSaid;
          again = last.end === "noanswer" || handAlive() ? B.filter(function (i) { return i.x.st === "nohand"; }) : [];
        } else if (last.end === REFUSED) {             // 아무것도 넘기지 못했다 — 까닭은 일마다 같은 한 줄이다. 못 한 줄은 다시 맡길 수 있다
          chipText = W.nohand; chipCls = "no"; saidCls = "no";
          var why = B.filter(function (i) { return i.x.st === "failed" && i.x.rec && i.x.rec.said; })[0];
          said = why ? why.x.rec.said : W.noanswerSaid;
        } else if (last.end === "session" || last.end === "stopped" || c.failed || c.unsure) {
          chipText = W.stopped; chipCls = "no"; saidCls = "no";
          said = fmt(last.end === "session" ? W.login : last.end === "stopped" ? W.died : W.partly, { t: t, counts: counts(c) });
        } else if (c.asked) {
          chipText = fmt(W.asked, { n: c.asked }); chipCls = "need"; saidCls = "need";
          said = fmt(W.askedSaid, { d: c.done, n: c.asked, t: hm(askedRows[0].x.rec.at), c: askedRows.map(function (i) { return cardOf(i.row); }).join(" · ") });
        } else if (c.calWait) {                        // 맡긴 일은 다 됐고 「일정 넣기」만 제 손을 기다린다 — 그 줄의 말이 까닭을 댄다
          chipText = fmt(W.running, { n: B.length, k: settled });
          chipCls = "wait";
          said = W.calWait;
        } else {
          chipText = fmt(W.done, { n: B.length, t: t }); chipCls = "ok";
          said = W.allDone + (teamsDone.length ? fmt(W.teams, { c: teamsDone.join(" · ") }) : "");
        }
      }
      var one = singles(infos, batchRuns);
      if (one && (liveMode || !c.busy && !c.lost)) {   // 따로 맡긴 줄 — 판이 돌지 않는 동안 막대가 그 줄의 지금을 말한다(앞 판의 끝을 그대로 들지 않는다)
        chipText = one.chip === undefined ? chipText : one.chip; chipCls = one.cls; said = one.said; saidCls = one.cls === "no" ? "no" : "";
      }
      // 표시해 맡길 줄이 없고 막대가 말할 거리도 없으면 막대와 그리로 가는 닻을 안 세운다 — 「0건 · 표시한 0건 맡기기」는 누를 것이 없는 단추다.
      // 「일정 넣기」 줄은 제 누름으로 넣고 그 끝은 카드가 말한다
      var nothing = liveMode && !on.length && !off.length && !one;
      var toBoard = document.querySelector('.toc a[href="#board"]');
      if (toBoard) toBoard.parentNode.hidden = nothing;
      if (nothing) {
        boards.forEach(function (bd) { bd.hidden = true; });
        return liveMode;
      }
      boards.forEach(function (bd) {
        bd.hidden = false;
        bd.querySelector(".bar-n").textContent = nText;
        var kk = bd.querySelector(".bar-kinds");
        kk.textContent = kinds;
        kk.hidden = !kinds;
        var chip = bd.querySelector(".bar-st");
        chip.hidden = !chipText;
        chip.textContent = chipText;
        chip.className = "st bar-st" + (chipCls ? " " + chipCls : "");
        var go = bd.querySelector(".board-go");
        go.hidden = !(liveMode || again.length);
        go.textContent = liveMode ? goText : fmt(W.again, { n: again.length });
        go.disabled = liveMode ? goOff : false;
        go.onclick = function () { pressTasks(liveMode ? "batch" : "again", liveMode ? null : again); };
        var s = bd.querySelector(".board-said"), h = bd.querySelector(".bar-hint");
        s.hidden = !said;
        s.textContent = said;
        s.className = "board-said" + (saidCls ? " " + saidCls : "");
        h.hidden = !!said || !liveMode;
        var l = bd.querySelector(".end-left");
        if (l) {
          l.hidden = !(liveMode && left);
          l.textContent = left;
        }
      });
      return liveMode;
    }

    // 누름 — batch(표시한 것 · 위에서부터) · again(못 한 것) · card(그 줄 하나). 「일정 넣기」 줄은 제 누름을 남기고, 나머지는 누름 하나에 차례대로
    function pressTasks(how, rowsGiven) {
      var runs = allRuns(), list;
      if (how === "batch") {
        list = taskRows.map(function (r) { return { row: r, id: r.getAttribute("data-t"), x: rowState(r, runs) }; })
          .filter(function (i) { return rehandable(i.x.st) && ticked[i.id] !== false; });
      } else {
        list = rowsGiven;
      }
      if (!list.length) return;
      var ids = [], cal = [];
      try {
        list.forEach(function (i) {
          var b = i.row.querySelector("button.put[data-key]");
          if (b) { Cal.press(b); cal.push(i.id); } else ids.push(i.id);
        });
        if (how !== "card" || ids.length) {
          var now = new Date(), rec = { at: now.toISOString(), brief: pageName(), ids: ids, cal: cal, how: how };
          if (!ids.length) { rec.ended = rec.at; rec.end = "done"; }            // 「일정 넣기」뿐인 누름 — 손이 맡을 일이 없다
          else if (!handAlive()) { rec.ended = rec.at; rec.end = "nohand"; }
          store.setItem(RUN + pageName() + "~" + now.getTime(), JSON.stringify(rec));
        }
      } catch (e) {
        var said = document.querySelector(".board-said");
        if (said) { said.hidden = false; said.textContent = "누름을 못 남겼습니다 — 대화에서 말씀해 주세요"; said.className = "board-said no"; }
        return;
      }
      if (how !== "card") pressedHere = true;
      paintAll();
    }

    function paintTalks() {
      var v = Ask.record(), waiting = Ask.waiting(), here = Ask.here();
      talkRows.forEach(function (row) {
        var b = row.querySelector(".talk-go");
        if (!b) return;
        var id = row.getAttribute("data-talk"), mine = v && v.task === id, note = row.nextElementSibling, said = "";
        b.hidden = false;
        if (mine && !v.done && waiting) { b.textContent = W.opening; b.disabled = true; }
        else if (mine && v.done && v.state === "opened") { b.textContent = fmt(W.opened, { t: hm(v.done) }); b.disabled = true; }
        else {
          b.textContent = W.talk;
          b.disabled = waiting;
          said = here && here.task === id ? here.said : mine && v.done ? v.said || "" : "";
        }
        note.textContent = said;
        note.className = "put-note" + (said ? " no" : "");
      });
    }

    function paintTasks() {
      var runs = allRuns();
      var infos = taskRows.map(function (r) { return { row: r, id: r.getAttribute("data-t"), x: rowState(r, runs) }; });
      var liveMode = boards.length ? paintBoards(infos, runs) : false;
      var byId = {};
      infos.forEach(function (i) { byId[i.id] = i; paintRow(i.row, i.x, liveMode); });
      if (topBoard) {
        Array.prototype.forEach.call(topBoard.querySelectorAll(".brow[data-t]"), function (li) {
          var i = byId[li.getAttribute("data-t")];
          if (i) paintBrow(li, i.row, i.x, liveMode);
        });
      }
      paintTalks();
      tasksBusy = runs.some(function (r) { return !r.v.ended; }) || infos.some(function (i) { return i.x.st === "wait"; });
    }

    if (taskRows.length || talkRows.length) {
      document.addEventListener("change", function (e) {
        var i = e.target;
        if (!i.matches || !i.matches("input[data-t]")) return;
        ticked[i.getAttribute("data-t")] = i.checked;
        paintTasks();
      });
      taskRows.forEach(function (row) {
        row.querySelector("button.put").addEventListener("click", function () {
          var runs = allRuns(), x = rowState(row, runs);
          if (x.cancel) {
            try { Cal.cancel(row.querySelector("button.put[data-key]")); } catch (e) { /* 못 지워도 그린 것은 같다 */ }
            paintAll();
          } else if (x.st === "idle" || x.st === "failed" || x.st === "nohand") {
            pressTasks("card", [{ row: row, id: row.getAttribute("data-t"), x: x }]);
          }
        });
      });
      talkRows.forEach(function (row) {
        var b = row.querySelector(".talk-go");
        if (b) b.addEventListener("click", function () { Ask.send(row.getAttribute("data-words"), row.getAttribute("data-talk"), ""); });
      });
      if (topBoard) {
        var tg = topBoard.querySelector(".bar-toggle");
        tg.addEventListener("click", function () {
          var o = topBoard.classList.toggle("is-open");
          tg.setAttribute("aria-expanded", o ? "true" : "false");
          tg.textContent = tg.getAttribute(o ? "data-close" : "data-open");
        });
      }
    }

    return { on: !!(taskRows.length || talkRows.length),
             paint: function () { if (taskRows.length || talkRows.length) paintTasks(); },
             tick: function () { if (tasksBusy) paintTasks(); },
             talks: paintTalks };
  })();

  // ── 다시 그리기 — 기능마다의 그리기를 차례대로 ──
  function paintAll() {
    Marks.paint();
    Times.paint();
    Lists.paint();
    Tasks.paint();
    Away.paint();
    Ask.paint();
    Appr.paint();
  }

  window.addEventListener("storage", paintAll);
  window.addEventListener("focus", paintAll);
  if (Tasks.on || Away.on || Times.on || Ask.on || Appr.on) {   // 걸린 누름 · 고름 · 부탁의 말이 손의 숨 표 · 흐른 때로 바뀐다 — 걸린 것이 없으면 안 그린다
    window.setInterval(function () {
      Tasks.tick();
      Away.tick();
      Times.tick();
      if (Appr.pending()) Appr.paint();
      if (Ask.pending()) {
        Ask.paint();
        Tasks.talks();
      }
    }, 2000);
  }
  paintAll();
})();
