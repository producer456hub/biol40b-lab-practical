/* BIOL 40B Lab Practical Trainer — exam engine */
(() => {
  const $ = id => document.getElementById(id);

  /* ---------- theme ---------- */
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("lp-theme");
  if (savedTheme) root.setAttribute("data-theme", savedTheme);
  $("theme").onclick = () => {
    const cur = root.getAttribute("data-theme")
      || (matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light");
    const nxt = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", nxt);
    localStorage.setItem("lp-theme", nxt);
  };

  /* ---------- answer normalization + fuzzy ---------- */
  const norm = s => s.toLowerCase().normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\b(the|a|an|of)\b/g, " ")
    .replace(/\s+/g, " ").trim();

  function lev(a, b) {
    const m = a.length, n = b.length;
    if (!m) return n; if (!n) return m;
    const d = Array.from({length: m + 1}, (_, i) => [i, ...Array(n).fill(0)]);
    for (let j = 0; j <= n; j++) d[0][j] = j;
    for (let i = 1; i <= m; i++)
      for (let j = 1; j <= n; j++)
        d[i][j] = Math.min(d[i-1][j]+1, d[i][j-1]+1,
          d[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
    return d[m][n];
  }
  // returns "correct" | "close" | "wrong"
  function judge(input, accepted) {
    const q = norm(input);
    if (!q) return "wrong";
    let best = 99, bestLen = 0;
    for (const a of accepted) {
      const t = norm(a);
      if (q === t) return "correct";
      const d = lev(q, t);
      if (d < best) { best = d; bestLen = t.length; }
    }
    // scale the spelling-nudge tolerance to answer length so short words
    // don't get a "so close" hint when a genuinely different word is typed
    const tol = bestLen <= 5 ? 1 : 2;
    return best <= tol ? "close" : "wrong";
  }

  /* ---------- build question pool ---------- */
  function buildQuestions(opts) {
    const qs = [];
    for (const s of SLIDES) {
      if (opts.whole) qs.push({
        kind: "whole", label: "Name the slide",
        prompt: "What tissue or slide is this?",
        image: "images/" + s.image, accepted: s.whole, answer: s.whole[0],
        title: s.title
      });
      if (opts.pin) for (const p of s.pins) qs.push({
        kind: "pin", label: "Identify",
        prompt: "Identify the structure marked by the target.",
        image: "images/" + s.image, x: p.x, y: p.y,
        accepted: p.accepted, answer: p.label, title: s.title
      });
    }
    const ARABIC = {I:"1",II:"2",III:"3",IV:"4",V:"5",VI:"6",VII:"7",VIII:"8",IX:"9",X:"10",XI:"11",XII:"12"};
    if (opts.cn) for (const c of CRANIAL) {
      // rotate through several strict-typeable question forms
      qs.push({kind:"fact", label:"Cranial nerve",
        prompt:`Cranial nerve ${c.n} is the ______ nerve.`,
        accepted:[c.name, c.name+" nerve"], answer:c.name});
      qs.push({kind:"fact", label:"Cranial nerve",
        prompt:`The ${c.name} nerve is cranial nerve number ______ (Roman numeral).`,
        accepted:[c.n, ARABIC[c.n]], answer:c.n});
      qs.push({kind:"fact", label:"Cranial nerve",
        prompt:`Is the ${c.name} nerve (CN ${c.n}) sensory, motor, or both?`,
        accepted: c.type==="both" ? ["both","mixed"] : [c.type], answer:c.type});
    }
    return qs;
  }

  const shuffle = a => { for (let i=a.length-1;i>0;i--){const j=Math.random()*(i+1)|0;[a[i],a[j]]=[a[j],a[i]];} return a; };

  /* ---------- state ---------- */
  let pool = [], idx = 0, retry = [], round = 1;
  let totalItems = 0, firstTry = 0, answeredFirst = new Set();
  let curKey = "", hinted = false, locked = false;

  const keyOf = q => q.kind + "|" + (q.title||"") + "|" + q.answer + "|" + (q.prompt);

  function start(opts) {
    const all = buildQuestions(opts);
    if (!all.length) return;
    pool = shuffle(all); idx = 0; retry = []; round = 1;
    totalItems = all.length; firstTry = 0; answeredFirst = new Set();
    show("exam");
    banner("");
    render();
  }

  function show(which) {
    for (const id of ["start","exam","done"]) $(id).classList.toggle("hidden", id !== which);
  }
  function banner(html){ $("banner").innerHTML = html; }

  /* ---------- render one question ---------- */
  function render() {
    locked = false; hinted = false;
    const q = pool[idx];
    curKey = keyOf(q);

    $("q-kind").textContent = q.label;
    $("q-prompt").textContent = q.prompt;

    const field = $("field"), img = $("q-img"), ret = $("reticle"), chip = $("chip");
    chip.innerHTML = "";
    if (q.image) {
      field.classList.remove("hidden");
      img.src = q.image;
      img.onload = () => positionReticle(q);
      if (q.kind === "pin") { positionReticle(q); }
      else ret.classList.add("hidden");
    } else {
      field.classList.add("hidden");
    }

    const inp = $("input");
    inp.value = ""; inp.className = ""; inp.disabled = false;
    $("feedback").className = "feedback"; $("feedback").innerHTML = "";
    $("next").classList.add("hidden");
    $("submit").classList.remove("hidden");
    ret.classList.remove("ok","bad");
    setTimeout(() => inp.focus(), 30);
    updateStatus();
  }

  function positionReticle(q) {
    const ret = $("reticle");
    if (q.kind !== "pin") { ret.classList.add("hidden"); return; }
    ret.classList.remove("hidden");
    ret.style.left = (q.x * 100) + "%";
    ret.style.top  = (q.y * 100) + "%";
  }

  function updateStatus() {
    $("s-round").textContent = round;
    $("s-left").textContent = pool.length - idx;
    $("s-retry").textContent = retry.length;
    const asked = answeredFirst.size;
    $("s-acc").textContent = asked ? Math.round(100 * firstTry / asked) + "%" : "—";
    const doneCount = idx;
    $("bar").style.width = (100 * doneCount / Math.max(1, pool.length)) + "%";
  }

  /* ---------- grading ---------- */
  function submit(e) {
    e.preventDefault();
    if (locked) return;
    const q = pool[idx];
    const verdict = judge($("input").value, q.accepted);
    const inp = $("input"), fb = $("feedback");

    if (verdict === "close" && !hinted) {
      hinted = true;
      inp.className = "hint";
      fb.className = "feedback hint";
      fb.innerHTML = "<b>So close</b> — check your spelling and try again.";
      inp.select();
      return;
    }

    const firstAttempt = !answeredFirst.has(curKey);
    if (firstAttempt) answeredFirst.add(curKey);
    locked = true;
    inp.disabled = true;
    $("submit").classList.add("hidden");
    $("next").classList.remove("hidden");
    $("next").focus();

    if (verdict === "correct") {
      if (firstAttempt && !hinted) firstTry++;
      inp.className = "ok";
      fb.className = "feedback ok";
      fb.innerHTML = "<b>Correct.</b> " + prettyAns(q);
      markReticle("ok", q, prettyLabel(q));
    } else {
      inp.className = "bad";
      fb.className = "feedback bad";
      fb.innerHTML = "<span class='ans'>" + prettyLabel(q) + "</span> — spelled exactly.";
      markReticle("bad", q, prettyLabel(q));
      // re-queue this question for a later round
      retry.push(q);
    }
    updateStatus();
  }

  function prettyLabel(q){ return q.answer; }
  function prettyAns(q){
    const extra = q.accepted.filter(a => norm(a) !== norm(q.answer));
    return extra.length ? "<span class='also'>also accepted: " + extra.join(", ") + "</span>" : "";
  }

  function markReticle(state, q, label) {
    const ret = $("reticle");
    if (q.kind === "pin" && q.image) {
      ret.classList.remove("hidden","ok","bad");
      ret.classList.add(state);
      const chip = $("chip");
      chip.innerHTML = "<span class='reveal-chip " + (state==="bad"?"bad":"") + "' style='left:" +
        (q.x*100) + "%;top:" + (q.y*100) + "%'>" + label + "</span>";
    }
  }

  /* ---------- advance ---------- */
  function next() {
    idx++;
    if (idx < pool.length) { render(); return; }
    // round complete
    if (retry.length === 0) return finish();
    round++;
    pool = shuffle(retry.slice());
    retry = [];
    idx = 0;
    banner(`<div class="banner"><span class="b-ico">🔁</span><div class="b-txt">
      <b>Round ${round}.</b> Reviewing the ${pool.length} item${pool.length>1?"s":""} you missed —
      keep going until every one is cleared.</div></div>`);
    render();
    // scroll banner into view on small screens
    window.scrollTo({top:0, behavior:"smooth"});
  }

  function finish() {
    show("done");
    $("done-ico").textContent = "✓";
    $("done-h").textContent = "Every structure cleared";
    $("done-p").textContent = firstTry === totalItems
      ? "A clean sweep — you nailed all " + totalItems + " on the first try."
      : "You worked through every miss until nothing was left. That's mastery.";
    $("d-items").textContent = totalItems;
    $("d-first").textContent = firstTry;
    $("d-rounds").textContent = round;
  }

  /* ---------- lightbox ---------- */
  $("field").onclick = (e) => {
    const q = pool[idx]; if (!q || !q.image) return;
    $("lb-img").src = q.image;
    const lr = $("lb-reticle");
    if (q.kind === "pin") {
      lr.classList.remove("hidden");
      lr.style.left = (q.x * 100) + "%";
      lr.style.top  = (q.y * 100) + "%";
    } else lr.classList.add("hidden");
    $("lightbox").classList.add("on");
  };
  $("lightbox").onclick = () => $("lightbox").classList.remove("on");

  /* ---------- wire up ---------- */
  $("startBtn").onclick = () => start({
    pin: $("opt-pin").checked,
    whole: $("opt-whole").checked,
    cn: $("opt-cn").checked,
  });
  $("answer").addEventListener("submit", submit);
  $("next").onclick = next;
  $("quit").onclick = () => { show("start"); banner(""); };
  $("again").onclick = () => show("start");

  // guard: need at least one option
  for (const id of ["opt-pin","opt-whole","opt-cn"])
    $(id).addEventListener("change", () => {
      const any = $("opt-pin").checked || $("opt-whole").checked || $("opt-cn").checked;
      $("startBtn").disabled = !any;
      $("startBtn").style.opacity = any ? "1" : ".5";
    });
})();
