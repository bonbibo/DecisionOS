/* Luupie — dokunma / swipe algılama */
"use strict";

const Input = {
  onTap: null,     // (x, y) stage koordinatı
  onSwipe: null,   // (dir, info)  dir: "up"|"down"|"left"|"right"
  _start: null,

  init: function (stageEl) {
    const opts = { passive: false };

    function toStage(clientX, clientY) {
      const rect = stageEl.getBoundingClientRect();
      return {
        x: (clientX - rect.left) / rect.width * CONFIG.designW,
        y: (clientY - rect.top) / rect.height * CONFIG.designH,
      };
    }

    function down(cx, cy, target) {
      Input._start = { p: toStage(cx, cy), t: performance.now(), target: target };
    }

    function up(cx, cy) {
      if (!Input._start) return;
      const s = Input._start; Input._start = null;
      const p = toStage(cx, cy);
      const dx = p.x - s.p.x, dy = p.y - s.p.y;
      const dist = Math.hypot(dx, dy);
      if (dist < 24) {
        if (Input.onTap) Input.onTap(s.p.x, s.p.y, s.target);
        return;
      }
      let dir;
      if (Math.abs(dx) > Math.abs(dy)) dir = dx > 0 ? "right" : "left";
      else dir = dy > 0 ? "down" : "up";
      if (Input.onSwipe) Input.onSwipe(dir, { dx: dx, dy: dy, start: s.p, end: p });
    }

    stageEl.addEventListener("touchstart", function (e) {
      if (e.target.closest("button")) return;
      e.preventDefault();
      const t = e.changedTouches[0];
      down(t.clientX, t.clientY, e.target);
    }, opts);
    stageEl.addEventListener("touchend", function (e) {
      if (e.target.closest("button")) return;
      e.preventDefault();
      const t = e.changedTouches[0];
      up(t.clientX, t.clientY);
    }, opts);

    stageEl.addEventListener("mousedown", function (e) {
      if (e.target.closest("button")) return;
      e.preventDefault();   // masaüstünde metin/görsel sürüklemesini engelle
      down(e.clientX, e.clientY, e.target);
    });
    stageEl.addEventListener("dragstart", function (e) { e.preventDefault(); });
    stageEl.addEventListener("mouseup", function (e) {
      if (e.target.closest("button")) return;
      up(e.clientX, e.clientY);
    });
  },
};

/* ufak WebAudio efektleri (asset istemez) */
const Sfx = {
  ctx: null,
  _ensure: function () {
    if (!Sfx.ctx) {
      try { Sfx.ctx = new (window.AudioContext || window.webkitAudioContext)(); }
      catch (e) { Sfx.ctx = null; }
    }
    return Sfx.ctx;
  },
  _beep: function (freq, dur, type, gain) {
    const ctx = Sfx._ensure();
    if (!ctx) return;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type || "sine"; o.frequency.value = freq;
    g.gain.value = gain || 0.06;
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + dur);
    o.connect(g); g.connect(ctx.destination);
    o.start(); o.stop(ctx.currentTime + dur);
  },
  tap: function () { Sfx._beep(500, 0.07, "triangle"); },
  good: function () { Sfx._beep(660, 0.12, "triangle"); Sfx._beep(880, 0.18, "sine"); },
  bad: function () { Sfx._beep(180, 0.25, "sawtooth", 0.05); },
  coin: function () { Sfx._beep(990, 0.09, "square", 0.04); },
  psycho: function () { Sfx._beep(120, 0.4, "sawtooth", 0.06); Sfx._beep(90, 0.5, "square", 0.04); },
};
