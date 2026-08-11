/* Luupie — açılış, oyun döngüsü, ölçekleme, girdi yönlendirme */
"use strict";

(function () {
  const stage = document.getElementById("stage");
  const canvas = document.getElementById("world");
  const ctx = canvas.getContext("2d");
  let RES = 1;

  function resize() {
    // stage'i pencereye sığdır (dikey oyun; letterbox)
    const scale = Math.min(
      window.innerWidth / CONFIG.designW,
      window.innerHeight / CONFIG.designH
    );
    stage.style.transform = "translate(-50%,-50%) scale(" + scale + ")";
    stage.style.marginLeft = "0";
    stage.style.marginTop = "0";

    RES = Math.min(3, (window.devicePixelRatio || 1) * Math.max(1, scale));
    canvas.width = Math.round(CONFIG.designW * RES);
    canvas.height = Math.round(CONFIG.designH * RES);
  }
  window.addEventListener("resize", resize);
  resize();

  /* ---------- rastgele olaylar ---------- */
  let nextBreakdown = performance.now() + 60000 + Math.random() * 120000;
  const repairBadge = document.getElementById("repair-badge");
  // rozeti bandın orta noktasına oturt (iso ayarları değişse de takip etsin)
  (function placeBadge() {
    const a = Iso.toScreen(0.2, 0.2), b = Iso.toScreen(0.2, Iso.grid - 1.4);
    repairBadge.style.left = ((a.x + b.x) / 2) + "px";
    repairBadge.style.top = ((a.y + b.y) / 2 - 78) + "px";
  })();

  repairBadge.addEventListener("click", function () {
    Sfx.tap();
    UI.closeAll();
    Minigames.openRepair();
  });

  function randomEvents(now) {
    if (!Factory.conveyorBroken && now > nextBreakdown && !Minigames.isOpen()) {
      Factory.conveyorBroken = true;
      Sfx.bad();
      UI.toast("⚠️ Konveyör arızalandı! Üretim yarıya düştü — 🔧 rozetine dokun!");
      nextBreakdown = now + 240000 + Math.random() * 240000;
    }
    // rozet görünürlüğü canvas durumunu takip eder
    const wantBadge = Factory.conveyorBroken && !Minigames.isOpen();
    repairBadge.classList.toggle("hidden", !wantBadge);
  }

  /* ---------- girdi ---------- */
  Input.onTap = function (x, y, target) {
    if (Minigames.isOpen()) return;
    if (target && target.closest && (target.closest("#panel") || target.closest("#char-popup") || target.closest("#dock"))) return;

    // karakter seçimi (öndekiler öncelikli)
    const sorted = Game.ponchiqs.slice().sort(function (a, b) {
      return b.screenPos().y - a.screenPos().y;
    });
    for (let k = 0; k < sorted.length; k++) {
      if (sorted[k].hitTest(x, y)) {
        Sfx.tap();
        UI.hidePanel();
        UI.showPopup(sorted[k]);
        return;
      }
    }

    if (Factory.conveyorBroken && Factory.conveyorHit(x, y)) {
      Sfx.tap();
      UI.closeAll();
      Minigames.openRepair();
      return;
    }

    UI.hidePopup();
  };

  Input.onSwipe = function (dir) {
    if (Minigames.isOpen()) Minigames.onSwipe(dir);
  };

  /* ---------- döngü ---------- */
  let lastT = performance.now();

  function frame(now) {
    const dt = Math.min(0.1, (now - lastT) / 1000);
    lastT = now;

    Game.update(dt);
    randomEvents(now);

    // çizim
    ctx.setTransform(RES, 0, 0, RES, 0, 0);
    ctx.clearRect(0, 0, CONFIG.designW, CONFIG.designH);
    ctx.drawImage(Factory.staticLayer, 0, 0);
    Factory.drawAnimated(ctx, now);

    // derinlik sırasına göre karakterler
    const drawList = Game.ponchiqs.slice().sort(function (a, b) {
      return a.screenPos().y - b.screenPos().y;
    });
    drawList.forEach(function (p) { p.draw(ctx, now); });

    Game.drawFloaters(ctx);
    Factory.drawVignette(ctx);

    // popup açıksa sevgi barını canlı tut
    if (UI.selected) UI._refreshLove(UI.selected);

    requestAnimationFrame(frame);
  }

  /* ---------- başlat ---------- */
  function boot() {
    Factory.init();
    Minigames.init();
    UI.init();
    Input.init(stage);

    const loaded = Game.load();
    if (!loaded) {
      Game.freshStart();
      UI.toast("Luupie Fabrikası'na hoş geldin! Karakterlere dokun. 💖");
    } else {
      const offline = Game.applyOffline();
      if (offline && (offline.products > 0 || offline.newPsycho > 0)) {
        UI.showWelcome(offline);
      }
      Game.save();
    }

    UI.refreshHud();
    setInterval(function () { Game.save(); }, 5000);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") Game.save();
    });

    requestAnimationFrame(frame);
  }

  Assets.load(boot);
})();
