// Draws docs/data/runs.json, which scripts/make_page_data.py builds from the
// committed EvalReport dumps in benchmarks/v0.1.0/. The only figure computed
// rather than copied is the Wilson interval, and that is computed in Python so
// it can be checked outside a browser.

const el = (id) => document.getElementById(id);
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

const state = { data: null, suite: null, metric: 'cost' };

const METRICS = {
  cost: {
    label: 'Cost',
    get: (t) => t.cost_usd,
    fmt: (v) => (v < 0.001 ? `$${v.toFixed(5)}` : `$${v.toFixed(4)}`),
    axis: 'cost in dollars',
  },
  latency: {
    label: 'Latency',
    get: (t) => t.latency_ms,
    fmt: (v) => `${Math.round(v).toLocaleString('en-US')} ms`,
    axis: 'latency in milliseconds',
  },
};
const metric = () => METRICS[state.metric];

const run = () => state.data.runs.find((r) => r.suite === state.suite);
const usd = (v) => `$${v.toFixed(5)}`;
const pctf = (v) => `${(v * 100).toFixed(0)}%`;

function labelOnPaper(ctx, text, x, y, align = 'center') {
  const w = ctx.measureText(text).width;
  const left = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  const prev = ctx.fillStyle;
  ctx.fillStyle = css('--paper');
  ctx.fillRect(left - 3, y - 11, w + 6, 14);
  ctx.fillStyle = prev;
  ctx.textAlign = align;
  ctx.fillText(text, x, y);
}

function fitCanvas(canvas, h0) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w0 = canvas.clientWidth || 1200;
  canvas.width = Math.round(w0 * dpr);
  canvas.height = Math.round(h0 * dpr);
  canvas.style.height = h0 + 'px';
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w0, h0);
  return { ctx, w: w0, h: h0 };
}

// ------------------------------------------------- figure 1: accuracy + CI

function drawAcc() {
  const rows = state.data.runs;
  const { ctx, w, h } = fitCanvas(el('plot-acc'), 210);
  const pad = { l: 148, r: 68, t: 18, b: 42 };
  const iw = w - pad.l - pad.r;
  const rowH = (h - pad.t - pad.b) / rows.length;
  const X = (v) => pad.l + v * iw;

  ctx.font = "11px 'Courier New', monospace";
  ctx.textAlign = 'center';
  for (let v = 0; v <= 1.0001; v += 0.25) {
    ctx.strokeStyle = css('--grid');
    ctx.beginPath(); ctx.moveTo(X(v), pad.t); ctx.lineTo(X(v), pad.t + rows.length * rowH); ctx.stroke();
    ctx.fillStyle = css('--faint');
    ctx.fillText(pctf(v), X(v), h - 22);
  }

  rows.forEach((r, i) => {
    const y = pad.t + i * rowH + rowH / 2;
    // The interval first, as a rule, then the point estimate on top of it.
    ctx.strokeStyle = css('--ox-dim');
    ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(X(r.wilson_lo), y); ctx.lineTo(X(r.wilson_hi), y); ctx.stroke();
    ctx.strokeStyle = css('--ox');
    ctx.lineWidth = 1.5;
    [r.wilson_lo, r.wilson_hi].forEach((v) => {
      ctx.beginPath(); ctx.moveTo(X(v), y - 7); ctx.lineTo(X(v), y + 7); ctx.stroke();
    });
    ctx.beginPath();
    ctx.arc(X(r.accuracy), y, 5, 0, Math.PI * 2);
    ctx.fillStyle = css('--ox');
    ctx.fill();
    if (r.suite === state.suite) {
      ctx.strokeStyle = css('--ink');
      ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(X(r.accuracy), y, 8, 0, Math.PI * 2); ctx.stroke();
    }

    ctx.textAlign = 'right';
    ctx.font = "13px 'Times New Roman', serif";
    ctx.fillStyle = r.suite === state.suite ? css('--ink') : css('--sub');
    ctx.fillText(r.suite.replace(/_/g, ' '), pad.l - 12, y + 4);
    ctx.textAlign = 'left';
    ctx.fillStyle = css('--sub');
    ctx.font = "12px 'Times New Roman', serif";
    ctx.fillText(`${r.n_correct}/${r.n_tasks}`, pad.l + iw + 10, y + 4);
  });

  ctx.textAlign = 'left';
  ctx.fillStyle = css('--faint');
  ctx.font = "11px 'Courier New', monospace";
  ctx.fillText('dot: measured accuracy   bar: 95% Wilson interval', pad.l, h - 6);
}

function renderAcc() {
  const r = run();
  el('r-acc').textContent = r.accuracy.toFixed(2);
  el('r-ci').textContent = `${r.wilson_lo.toFixed(2)} to ${r.wilson_hi.toFixed(2)}`;
  el('r-n').textContent = `${r.n_correct} of ${r.n_tasks}`;
  el('r-cpc').textContent = usd(r.cost_per_correct_answer);
  el('r-lat').textContent = `${Math.round(r.p50_latency_ms)} / ${Math.round(r.p95_latency_ms)} ms`;
  el('cap-what').textContent = `${r.agent} on ${state.data.runs.length} suites, v${state.data.suite_version}`;
  el('cap-judge').textContent = `judged by ${r.judge_model}`;
  drawAcc();

  const width = r.wilson_hi - r.wilson_lo;
  const b = el('acc-banner');
  b.className = width > 0.25 ? 'banner alarm' : 'banner';
  b.textContent =
    r.accuracy === 1
      ? `${r.n_correct} of ${r.n_tasks}, so the interval runs from ${r.wilson_lo.toFixed(2)} to 1.00. ` +
        `No failures in ${r.n_tasks} tries is not the same claim as a perfect model.`
      : `${r.n_correct} of ${r.n_tasks}. The interval is ${(width * 100).toFixed(0)} points wide, which is ` +
        `what a run this size buys.`;
  drawTasks();
}

// ------------------------------------------------------ figure 2: per task

function drawTasks() {
  const r = run();
  const tasks = r.tasks;
  const m = metric();
  const { ctx, w, h } = fitCanvas(el('plot-tasks'), 240);
  const pad = { l: 86, r: 26, t: 22, b: 52 };
  const iw = w - pad.l - pad.r;
  const ih = h - pad.t - pad.b;
  const top = Math.max(...tasks.map(m.get)) * 1.15;
  const X = (i) => pad.l + ((i + 0.5) / tasks.length) * iw;
  const Y = (v) => pad.t + ih - (v / top) * ih;

  ctx.strokeStyle = css('--hair');
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t); ctx.lineTo(pad.l, pad.t + ih); ctx.lineTo(pad.l + iw, pad.t + ih);
  ctx.stroke();
  ctx.font = "11px 'Courier New', monospace";
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const v = (top / 4) * i;
    ctx.fillStyle = css('--faint');
    ctx.fillText(m.fmt(v), pad.l - 8, Y(v) + 3);
    if (i) {
      ctx.strokeStyle = css('--grid');
      ctx.beginPath(); ctx.moveTo(pad.l, Y(v)); ctx.lineTo(pad.l + iw, Y(v)); ctx.stroke();
    }
  }

  const bw = Math.min((iw / tasks.length) * 0.55, 26);
  tasks.forEach((t, i) => {
    const x = X(i) - bw / 2;
    const y = Y(m.get(t));
    ctx.fillStyle = css('--ox');
    if (t.correct) {
      ctx.fillRect(x, y, bw, pad.t + ih - y);
    } else {
      // Hollow where the judge said no, so wrong answers read without colour.
      ctx.strokeStyle = css('--bad');
      ctx.lineWidth = 1.8;
      ctx.strokeRect(x + 0.9, y + 0.9, bw - 1.8, pad.t + ih - y - 1.8);
    }
  });

  const dear = tasks.reduce((a, b) => (m.get(b) > m.get(a) ? b : a));
  const cheap = tasks.reduce((a, b) => (m.get(b) < m.get(a) ? b : a));
  ctx.font = "12px 'Times New Roman', serif";
  ctx.fillStyle = css('--sub');
  labelOnPaper(ctx, dear.task_id, X(tasks.indexOf(dear)), Y(m.get(dear)) - 8);

  ctx.textAlign = 'left';
  ctx.fillStyle = css('--faint');
  ctx.font = "11px 'Courier New', monospace";
  ctx.fillText(`${tasks.length} tasks, left to right, ${m.axis}`, pad.l, h - 30);
  ctx.fillText('hollow with a red edge: the judge marked it wrong', pad.l, h - 14);

  el('cap-tasks').textContent = `${r.suite.replace(/_/g, ' ')}, ${tasks.length} tasks`;
  const ratio = m.get(dear) / Math.max(m.get(cheap), 1e-9);
  const b = el('task-banner');
  if (state.metric === 'latency') {
    // With ten samples a p95 sits between the ninth and tenth, so it can report
    // a number no task actually took. Say so where the number is shown.
    const sorted = tasks.map(m.get).sort((x, y) => x - y);
    const second = sorted[sorted.length - 2];
    const gap = r.p95_latency_ms > second && r.p95_latency_ms < m.get(dear);
    b.className = gap ? 'banner alarm' : 'banner';
    b.textContent = gap
      ? `The slowest task took ${m.fmt(m.get(dear))} and the next slowest ${m.fmt(second)}. ` +
        `The reported p95 of ${m.fmt(r.p95_latency_ms)} falls in the gap between them: with ` +
        `${tasks.length} samples it is an interpolation, not an observation.`
      : `Slowest task ${m.fmt(m.get(dear))} against ${m.fmt(m.get(cheap))} for the fastest, ` +
        `${ratio.toFixed(1)}x. Reported p50 is ${m.fmt(r.p50_latency_ms)}.`;
  } else {
    b.className = 'banner';
    b.textContent =
      `Within this suite the dearest task cost ${ratio.toFixed(1)}x the cheapest ` +
      `(${m.fmt(m.get(dear))} against ${m.fmt(m.get(cheap))}). An average over ${tasks.length} tasks ` +
      `hides that, which is why cost per correct answer is the reported figure.`;
  }
}

// -------------------------------------------------------------- the void run

function voidRun() {
  const v = state.data.void[0];
  if (!v) { el('void').style.display = 'none'; return; }
  el('void').innerHTML =
    `<div class="tag">void run, not published as a result</div>` +
    `<p><strong>${v.file}</strong> reports ${v.accuracy.toFixed(2)} accuracy on ${v.suite.replace(/_/g, ' ')}. ` +
    `It is not a measurement of that model: ${v.n_errored} of its ${v.n_tasks} calls came back as ` +
    `${v.error_kind} against a free-tier quota and returned nothing, and the harness scores an ` +
    `empty answer 0.0. The repository lists the multi-model rows as pending for this reason.</p>`;
}

function picker(node, items, current, onPick) {
  node.innerHTML = '';
  items.forEach(({ key, label }) => {
    const b = document.createElement('button');
    b.textContent = label;
    b.setAttribute('aria-pressed', String(key === current()));
    b.addEventListener('click', () => {
      onPick(key);
      [...node.children].forEach((c) => c.setAttribute('aria-pressed', String(c === b)));
    });
    node.appendChild(b);
  });
}

async function main() {
  const res = await fetch('./data/runs.json');
  if (!res.ok) {
    el('acc-banner').textContent = `Could not load the runs (HTTP ${res.status}).`;
    return;
  }
  state.data = await res.json();
  state.suite = state.data.runs[0].suite;

  picker(
    el('metrics'),
    Object.entries(METRICS).map(([k, v]) => ({ key: k, label: v.label })),
    () => state.metric,
    (k) => { state.metric = k; drawTasks(); },
  );
  picker(
    el('suites'),
    state.data.runs.map((r) => ({ key: r.suite, label: r.suite.replace(/_/g, ' ') })),
    () => state.suite,
    (k) => { state.suite = k; renderAcc(); },
  );
  window.addEventListener('resize', () => { drawAcc(); drawTasks(); });

  renderAcc();
  voidRun();
}

main();
