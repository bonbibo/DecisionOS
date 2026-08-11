/* Luupie — swipe tabanlı 3 mini oyun */
"use strict";

const ARROWS = { up: "⬆️", down: "⬇️", left: "⬅️", right: "➡️" };
const DIRS = ["up", "down", "left", "right"];

const Minigames = {
  active: null,       // {type, state, tick}
  _interval: null,

  overlayEl: null, titleEl: null, bodyEl: null,

  init: function () {
    Minigames.overlayEl = document.getElementById("overlay");
    Minigames.titleEl = document.getElementById("og-title");
    Minigames.bodyEl = document.getElementById("og-body");
  },

  isOpen: function () { return !!Minigames.active; },

  _open: function (type, title) {
    Minigames.active = { type: type };
    Minigames.titleEl.textContent = title;
    Minigames.bodyEl.innerHTML = "";
    Minigames.overlayEl.classList.remove("hidden");
  },

  close: function () {
    Minigames.active = null;
    if (Minigames._interval) { clearInterval(Minigames._interval); Minigames._interval = null; }
    Minigames.overlayEl.classList.add("hidden");
  },

  onSwipe: function (dir) {
    const a = Minigames.active;
    if (!a) return;
    if (a.type === "trouble") Minigames._troubleSwipe(dir);
    else if (a.type === "repair") Minigames._repairSwipe(dir);
    else if (a.type === "cafeteria") Minigames._cafSwipe(dir);
  },

  /* =========================================================
     1) TOY TROUBLE — psycho zapt etme (push-your-luck)
     ========================================================= */
  openTrouble: function (ponchiq) {
    Minigames._open("trouble", "OYUNCAK KRİZİ!");
    const a = Minigames.active;
    a.ponchiq = ponchiq;
    a.ladder = [1, 2, 4, 8];
    a.step = 0;
    a.baseReward = 40;
    a.phase = "intro";

    const img = Assets.spriteUrl(ponchiq.species, "psycho");
    Minigames.bodyEl.innerHTML =
      '<div class="mg-center mg-panel">' +
      '  <div class="mg-card" style="width:150px;height:150px"><img src="' + img + '" style="max-width:82%;max-height:82%"></div>' +
      '  <div class="mg-hint">' + ponchiq.name + " çıldırdı! Ok yönünde kaydırarak onu sakinleştir. Her doğru kaydırma çarpanı katlar: 1x → 2x → 4x → 8x</div>" +
      '  <div class="mg-buttons"><button class="go" id="mg-start">Başla!</button></div>' +
      "</div>";
    document.getElementById("mg-start").addEventListener("click", function () {
      Sfx.tap(); Minigames._troubleRound();
    });
  },

  _troubleRound: function () {
    const a = Minigames.active;
    a.phase = "arrow";
    a.dir = DIRS[(Math.random() * 4) | 0];
    a.windowMs = Math.max(550, 1200 - a.step * 160);
    a.roundStart = performance.now();

    const img = Assets.spriteUrl(a.ponchiq.species, "psycho");
    Minigames.bodyEl.innerHTML =
      '<div class="mg-center mg-panel">' +
      '  <div class="mg-mult">Çarpan: ' + a.ladder[a.step] + "x</div>" +
      '  <div class="mg-arrow" id="mg-arrow">' + ARROWS[a.dir] + "</div>" +
      '  <div class="mg-timerbar"><div id="mg-timer" style="width:100%"></div></div>' +
      '  <div class="mg-card" style="width:120px;height:120px"><img src="' + img + '" style="max-width:82%;max-height:82%"></div>' +
      '  <div class="mg-hint">Ok yönünde kaydır!</div>' +
      "</div>";

    if (Minigames._interval) clearInterval(Minigames._interval);
    Minigames._interval = setInterval(function () {
      const el = document.getElementById("mg-timer");
      if (!el || !Minigames.active) return;
      const left = 1 - (performance.now() - a.roundStart) / a.windowMs;
      el.style.width = Math.max(0, left * 100) + "%";
      if (left <= 0) Minigames._troubleFail("Süre doldu!");
    }, 40);
  },

  _troubleSwipe: function (dir) {
    const a = Minigames.active;
    if (a.phase !== "arrow") return;
    if (dir === a.dir) {
      Sfx.good();
      clearInterval(Minigames._interval); Minigames._interval = null;
      if (a.step >= a.ladder.length - 1) { Minigames._troubleWin(); return; }
      Minigames._troubleChoice();
    } else {
      Minigames._troubleFail("Yanlış yön!");
    }
  },

  _troubleChoice: function () {
    const a = Minigames.active;
    a.phase = "choice";
    const cur = a.baseReward * a.ladder[a.step];
    const next = a.baseReward * a.ladder[a.step + 1];
    Minigames.bodyEl.innerHTML =
      '<div class="mg-center mg-panel">' +
      '  <div class="mg-big">✨ ' + a.ladder[a.step] + "x!</div>" +
      '  <div class="mg-hint">Kasada: <b>' + cur + " 🪙</b><br>Devam edersen: " + next + " 🪙 — ama kaçırırsan hepsi gider!</div>" +
      '  <div class="mg-buttons">' +
      '    <button class="go" id="mg-continue">Riske Gir! (' + a.ladder[a.step + 1] + "x)</button>" +
      '    <button class="bank" id="mg-bank">Sakinleştir 🪙' + cur + "</button>" +
      "  </div>" +
      "</div>";
    document.getElementById("mg-continue").addEventListener("click", function () {
      Sfx.tap(); a.step++; Minigames._troubleRound();
    });
    document.getElementById("mg-bank").addEventListener("click", function () {
      Minigames._troubleWin();
    });
  },

  _troubleWin: function () {
    const a = Minigames.active;
    const reward = a.baseReward * a.ladder[a.step];
    Game.addCoins(reward);
    Game.addXP(25 + a.step * 15);
    a.ponchiq.love = Math.max(a.ponchiq.love, 70);
    a.ponchiq.form = "sweet";
    a.ponchiq.emote = { icon: "💖", until: performance.now() + 4000 };
    Sfx.coin();
    UI.toast(a.ponchiq.name + " zapt edildi! +" + reward + " 🪙");
    Minigames.close();
    Game.save();
  },

  _troubleFail: function (why) {
    const a = Minigames.active;
    clearInterval(Minigames._interval); Minigames._interval = null;
    Sfx.bad();
    a.ponchiq.lockedUntil = Date.now() + CONFIG.stationLockSec * 1000;
    a.ponchiq.emote = { icon: "😈", until: performance.now() + 4000 };
    a.phase = "fail";
    Minigames.bodyEl.innerHTML =
      '<div class="mg-center mg-panel">' +
      '  <div class="mg-big">💨 Kaçtı!</div>' +
      '  <div class="mg-hint">' + why + " " + a.ponchiq.name + " kaçtı; istasyon " + CONFIG.stationLockSec + " sn kilitli. Kayıp yok — sadece fırsat kaçtı!</div>" +
      '  <div class="mg-buttons"><button class="bank" id="mg-ok">Tamam</button></div>' +
      "</div>";
    document.getElementById("mg-ok").addEventListener("click", function () {
      Minigames.close(); Game.save();
    });
  },

  /* =========================================================
     2) TAMİR İSTASYONU — parça yerleştirme + dikiş
     ========================================================= */
  openRepair: function () {
    Minigames._open("repair", "TAMİR İSTASYONU");
    const a = Minigames.active;
    // onarılan oyuncak: nüfustan rastgele bir tür (kafası sprite'tan gelir)
    const pool = Game.ponchiqs.length ? Game.ponchiqs : SPECIES;
    const pick = pool[(Math.random() * pool.length) | 0];
    a.species = pick.species || pick.id;

    // Parça kenardan başlar, gövdeye doğru kaydırılır: yön = gidiş yönü.
    a.parts = [
      { key: "head", label: "kafa",     dir: "down",  x: 160, y: 30,  tx: 160, ty: 104 },
      { key: "armL", label: "sol kol",  dir: "right", x: 36,  y: 186, tx: 104, ty: 186 },
      { key: "armR", label: "sağ kol",  dir: "left",  x: 284, y: 186, tx: 216, ty: 186 },
      { key: "leg",  label: "bacaklar", dir: "up",    x: 160, y: 314, tx: 160, ty: 250 },
    ];
    a.idx = 0;
    a.phase = "parts";
    Minigames._repairRender();
  },

  // parçayı temsil eden görsel (kafa = tür sprite'ı, uzuvlar = çizim)
  _repairPartHtml: function (a, p, x, y, extraStyle) {
    const style = "left:" + x + "px;top:" + y + "px;" + (extraStyle || "");
    if (p.key === "head") {
      const url = Assets.spriteUrl(a.species, "head");
      return '<div class="rp rp-head" style="' + style + '"><img src="' + url + '"></div>';
    }
    if (p.key === "leg") {
      return '<div class="rp rp-legs" style="' + style + '"><i></i><i></i></div>';
    }
    return '<div class="rp rp-arm" style="' + style + '"></div>';
  },

  _repairRender: function () {
    const a = Minigames.active;
    let html = '<div class="repair-board" id="repair-board">';
    // gövde (dikiş izli peluş torso)
    html += '<div class="rp-torso"><span class="seam"></span></div>';

    a.parts.forEach(function (p, k) {
      if (p.done) {
        html += Minigames._repairPartHtml(a, p, p.tx, p.ty, "");
        return;
      }
      // hedef hayalet
      html += Minigames._repairPartHtml(a, p, p.tx, p.ty, "opacity:.22;");
      // sürüklenecek parça
      const active = k === a.idx;
      html += Minigames._repairPartHtml(a, p, p.x, p.y,
        active ? "filter:drop-shadow(0 0 10px #ffd35c);" : "opacity:.4;");
      if (active) {
        // ok parçanın üstünü kapatmasın: dikey hamlelerde yana, yatayda alta koy
        const off = { up: [62, 0], down: [62, 0], left: [0, 44], right: [0, 44] }[p.dir];
        html += '<div class="rp-cue" style="left:' + (p.x + off[0]) + "px;top:" + (p.y + off[1]) + 'px">' +
          ARROWS[p.dir] + "</div>";
      }
    });
    html += "</div>";

    const cur = a.parts[a.idx];
    html += '<div class="mg-center mg-panel" style="top:auto;bottom:96px;transform:translateX(-50%)">' +
      '<div class="mg-hint">' +
      (a.phase === "parts"
        ? "<b>" + cur.label + "</b> parçasını gövdeye doğru kaydır: " + ARROWS[cur.dir]
        : "Şimdi dik! Okları sırayla takip et:") +
      "</div>";
    if (a.phase === "stitch") {
      html += '<div class="stitch-path" style="position:static;margin-top:4px">';
      a.stitch.forEach(function (d, k) {
        const cls = k < a.stitchIdx ? "done" : (k === a.stitchIdx ? "active" : "");
        html += '<div class="stitch-step ' + cls + '">' + ARROWS[d] + "</div>";
      });
      html += "</div>";
    }
    html += "</div>";
    Minigames.bodyEl.innerHTML = html;
  },

  _repairSwipe: function (dir) {
    const a = Minigames.active;
    if (a.phase === "parts") {
      const cur = a.parts[a.idx];
      if (dir === cur.dir) {
        Sfx.good();
        cur.done = true;
        a.idx++;
        if (a.idx >= a.parts.length) {
          a.phase = "stitch";
          a.stitch = [];
          for (let k = 0; k < 5; k++) a.stitch.push(DIRS[(Math.random() * 4) | 0]);
          a.stitchIdx = 0;
        }
        Minigames._repairRender();
      } else {
        Sfx.bad();
        const board = document.getElementById("repair-board");
        if (board) {
          board.style.transition = "transform .08s";
          board.style.transform = "translate(-50%,-50%) translateX(6px)";
          setTimeout(function () { board.style.transform = "translate(-50%,-50%)"; }, 90);
        }
      }
    } else if (a.phase === "stitch") {
      if (dir === a.stitch[a.stitchIdx]) {
        Sfx.good();
        a.stitchIdx++;
        if (a.stitchIdx >= a.stitch.length) { Minigames._repairWin(); return; }
        Minigames._repairRender();
      } else {
        Sfx.bad();
        a.stitchIdx = Math.max(0, a.stitchIdx - 1);
        Minigames._repairRender();
      }
    }
  },

  _repairWin: function () {
    const reward = 120;
    Game.addCoins(reward);
    Game.addXP(40);
    if (Factory.conveyorBroken) {
      Factory.conveyorBroken = false;
      UI.toast("Konveyör tamir edildi! Üretim normale döndü. +" + reward + " 🪙");
    } else {
      UI.toast("Oyuncak onarıldı! +" + reward + " 🪙");
    }
    Sfx.coin();
    Minigames.close();
    Game.save();
  },

  /* =========================================================
     3) YEMEKHANE — doğru Luupie'ye yemek kaydır (refleks)
     ========================================================= */
  openCafeteria: function () {
    Minigames._open("cafeteria", "TATLI SERVİS!");
    const a = Minigames.active;
    a.round = 0;
    a.total = 6;
    a.hits = 0;
    a.streak = 0;
    Minigames._cafRound();
  },

  _cafRound: function () {
    const a = Minigames.active;
    if (a.round >= a.total) { Minigames._cafEnd(); return; }
    a.round++;
    a.phase = "play";

    // 4 yön için karakter seç (nüfustan; azsa türlerden tamamla)
    const pool = Game.ponchiqs.slice();
    while (pool.length < 4) {
      pool.push({ species: SPECIES[(Math.random() * SPECIES.length) | 0].id, name: "?", fake: true });
    }
    // karıştır
    for (let k = pool.length - 1; k > 0; k--) {
      const r = (Math.random() * (k + 1)) | 0;
      const tmp = pool[k]; pool[k] = pool[r]; pool[r] = tmp;
    }
    a.slots = { up: pool[0], left: pool[1], right: pool[2], down: pool[3] };
    a.craveDir = DIRS[(Math.random() * 4) | 0];
    a.food = FOODS[(Math.random() * FOODS.length) | 0];
    a.windowMs = Math.max(1400, 2600 - a.round * 220);
    a.roundStart = performance.now();

    const POS = {
      up: "left:50%;top:4%;transform:translateX(-50%)",
      left: "left:5%;top:31%",
      right: "right:5%;top:31%",
      down: "left:50%;top:58%;transform:translateX(-50%)",
    };
    let html = "";
    DIRS.forEach(function (d) {
      const p = a.slots[d];
      const url = Assets.spriteUrl(p.species, "head") || Assets.spriteUrl(p.species, "sweet");
      html += '<div class="mg-slot" id="slot-' + d + '" style="' + POS[d] + '"' +
        (d === a.craveDir ? ' data-food="' + a.food + '" ' : "") + ">" +
        '<img src="' + url + '"></div>';
    });
    html +=
      '<div class="mg-center mg-panel" style="top:40%">' +
      '  <div style="font-size:56px;filter:drop-shadow(0 4px 6px rgba(0,0,0,.5))">' + a.food + "</div>" +
      '  <div class="mg-timerbar"><div id="mg-timer" style="width:100%"></div></div>' +
      '  <div class="mg-hint">Tatlıyı isteyen Luupie\'ye kaydır! (' + a.round + "/" + a.total + ")</div>" +
      "</div>";
    Minigames.bodyEl.innerHTML = html;
    const crave = document.getElementById("slot-" + a.craveDir);
    if (crave) crave.classList.add("craving");

    if (Minigames._interval) clearInterval(Minigames._interval);
    Minigames._interval = setInterval(function () {
      const el = document.getElementById("mg-timer");
      if (!el || !Minigames.active) return;
      const left = 1 - (performance.now() - a.roundStart) / a.windowMs;
      el.style.width = Math.max(0, left * 100) + "%";
      if (left <= 0) Minigames._cafMiss();
    }, 40);
  },

  _cafSwipe: function (dir) {
    const a = Minigames.active;
    if (a.phase !== "play") return;
    clearInterval(Minigames._interval); Minigames._interval = null;
    if (dir === a.craveDir) {
      Sfx.good();
      a.hits++; a.streak++;
      const slot = document.getElementById("slot-" + dir);
      if (slot) slot.classList.add("correct");
      const p = a.slots[dir];
      if (!p.fake) {
        p.love = Math.min(100, p.love + 18);
        p.emote = { icon: "😋", until: performance.now() + 3000 };
      }
      a.phase = "wait";
      setTimeout(function () { if (Minigames.active) Minigames._cafRound(); }, 450);
    } else {
      Minigames._cafMiss();
    }
  },

  _cafMiss: function () {
    const a = Minigames.active;
    if (a.phase !== "play") return;
    clearInterval(Minigames._interval); Minigames._interval = null;
    Sfx.bad();
    a.streak = 0;
    a.phase = "wait";
    setTimeout(function () { if (Minigames.active) Minigames._cafRound(); }, 450);
  },

  _cafEnd: function () {
    const a = Minigames.active;
    const coins = a.hits * 15 + (a.hits === a.total ? 40 : 0);
    Game.addCoins(coins);
    Game.addXP(10 + a.hits * 6);
    Sfx.coin();
    Minigames.bodyEl.innerHTML =
      '<div class="mg-center mg-panel">' +
      '  <div class="mg-big">' + (a.hits === a.total ? "🌟 Mükemmel!" : "🍽️ Servis bitti!") + "</div>" +
      '  <div class="mg-hint">' + a.hits + "/" + a.total + " doğru servis · +" + coins + " 🪙<br>Beslenen Luupie'lerin sevgisi arttı!</div>" +
      '  <div class="mg-buttons"><button class="bank" id="mg-ok">Süper!</button></div>' +
      "</div>";
    document.getElementById("mg-ok").addEventListener("click", function () {
      Minigames.close(); Game.save();
    });
  },
};
