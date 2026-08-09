/* Luupie — HUD, paneller, popup, toast */
"use strict";

const UI = {
  selected: null,   // popup'ta gösterilen ponchiq

  init: function () {
    document.getElementById("btn-cafeteria").addEventListener("click", function () {
      Sfx.tap(); UI.closeAll(); Minigames.openCafeteria();
    });
    document.getElementById("btn-album").addEventListener("click", function () {
      Sfx.tap(); UI.showAlbum();
    });
    document.getElementById("btn-league").addEventListener("click", function () {
      Sfx.tap(); UI.showLeague();
    });
    document.getElementById("btn-adopt").addEventListener("click", function () {
      Sfx.tap(); UI.showAdopt();
    });
    document.getElementById("panel-close").addEventListener("click", function () {
      Sfx.tap(); UI.hidePanel();
    });
    document.getElementById("cp-close").addEventListener("click", function () {
      Sfx.tap(); UI.hidePopup();
    });
    document.getElementById("cp-action-main").addEventListener("click", function () {
      UI._popupAction();
    });
  },

  /* ---------- HUD ---------- */
  refreshHud: function () {
    document.getElementById("hud-coins").textContent = UI._fmt(Game.state.coins);
    document.getElementById("hud-products").textContent = UI._fmt(Game.state.products);
    document.getElementById("hud-level").textContent = Game.state.level;
    const need = Game.xpNeeded();
    document.getElementById("hud-xpbar").style.width =
      Math.min(100, Game.state.xp / need * 100) + "%";
  },

  _fmt: function (n) {
    n = Math.floor(n);
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 10000) return (n / 1000).toFixed(1) + "K";
    return String(n);
  },

  toast: function (msg) {
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    document.getElementById("toasts").appendChild(el);
    setTimeout(function () { el.remove(); }, 2800);
  },

  /* ---------- karakter popup ---------- */
  showPopup: function (p) {
    UI.selected = p;
    document.getElementById("cp-name").textContent =
      p.name + " · " + speciesById(p.species).name;
    const ageH = Math.floor(p.ageSec() / 3600);
    const gradH = Math.max(0, Math.ceil((CONFIG.graduationAgeSec - p.ageSec()) / 3600));
    document.getElementById("cp-stats").innerHTML =
      speciesById(p.species).personality + "<br>Yaş: " + ageH + " saat · Mezuniyete: " + gradH + " saat" +
      (p.form === "psycho" ? "<br><b style='color:#c9302c'>PSYCHO MODUNDA! (2x üretim, bulaşıcı)</b>" : "");
    const btn = document.getElementById("cp-action-main");
    if (p.form === "psycho") {
      btn.textContent = p.isLocked() ? "İstasyon kilitli 🔒" : "Zapt Et! 💢";
      btn.disabled = p.isLocked();
    } else {
      btn.textContent = "Sev ❤️ (+8)";
      btn.disabled = false;
    }
    UI._refreshLove(p);
    document.getElementById("char-popup").classList.remove("hidden");
  },

  _refreshLove: function (p) {
    document.getElementById("cp-love").style.width = p.love + "%";
  },

  _popupAction: function () {
    const p = UI.selected;
    if (!p) return;
    if (p.form === "psycho") {
      if (p.isLocked()) { Sfx.bad(); return; }
      UI.hidePopup();
      Minigames.openTrouble(p);
    } else {
      Sfx.good();
      p.love = Math.min(100, p.love + 8);
      p.emote = { icon: "💖", until: performance.now() + 2500 };
      UI._refreshLove(p);
      Game.addXP(2);
      Game.save();
    }
  },

  hidePopup: function () {
    UI.selected = null;
    document.getElementById("char-popup").classList.add("hidden");
  },

  /* ---------- paneller ---------- */
  _panel: function (title, bodyHtml) {
    document.getElementById("panel-title").textContent = title;
    document.getElementById("panel-body").innerHTML = bodyHtml;
    document.getElementById("panel").classList.remove("hidden");
  },

  hidePanel: function () {
    document.getElementById("panel").classList.add("hidden");
  },

  closeAll: function () {
    UI.hidePopup(); UI.hidePanel();
  },

  showAlbum: function () {
    const grads = Game.state.graduates;
    let html;
    if (!grads.length) {
      html = "<p style='text-align:center;padding:20px 8px'>Henüz mezun yok. Luupie'lerine iyi bak; " +
        Math.round(CONFIG.graduationAgeSec / 3600) + " saat sonra bir çocuk tarafından sahiplenilirler! 🎓</p>";
    } else {
      html = '<div class="album-grid">';
      grads.forEach(function (grd) {
        html += '<div class="album-item">' +
          '<img src="' + Assets.spriteUrl(grd.species, "head") + '">' +
          '<div class="nm">' + grd.name + "</div>" +
          '<div class="dt">' + new Date(grd.at).toLocaleDateString("tr-TR") + "</div>" +
          "</div>";
      });
      html += "</div>";
    }
    UI._panel("🎓 Mezunlar Albümü", html);
  },

  showLeague: function () {
    const rows = Game.leagueTable();
    let html = "<p style='text-align:center;margin-bottom:8px'>Haftalık Üretim Ligi — sadece <b>bu haftanın</b> üretimi sayılır!</p>";
    rows.forEach(function (r, k) {
      html += '<div class="league-row' + (r.me ? " me" : "") + '">' +
        '<div class="rank">' + (k + 1) + "</div>" +
        '<div class="nm">' + r.name + "</div>" +
        '<div class="sc">🧸 ' + UI._fmt(r.score) + "</div>" +
        "</div>";
    });
    UI._panel("🏆 Haftalık Lig", html);
  },

  showAdopt: function () {
    const count = Game.ponchiqs.length;
    const cost = Game.adoptCost();
    let html = "<p style='text-align:center;margin-bottom:8px'>Fabrika nüfusu: <b>" + count + " / " +
      CONFIG.maxPopulation + "</b> · Maliyet: <b>🪙 " + cost + "</b></p>";
    html += '<div class="adopt-grid">';
    SPECIES.forEach(function (s) {
      const locked = Game.state.level < s.unlockLevel;
      html += '<div class="adopt-item' + (locked ? " locked" : "") + '" data-species="' + s.id + '">' +
        '<img src="' + Assets.spriteUrl(s.id, "head") + '">' +
        '<div class="nm">' + s.name + "</div>" +
        '<div class="pr">' + (locked ? "Seviye " + s.unlockLevel : s.personality) + "</div>" +
        "</div>";
    });
    html += "</div>";
    UI._panel("➕ Yeni Luupie Sahiplen", html);

    document.querySelectorAll(".adopt-item").forEach(function (el) {
      el.addEventListener("click", function () {
        if (el.classList.contains("locked")) { Sfx.bad(); return; }
        const ok = Game.adopt(el.getAttribute("data-species"));
        if (ok) { UI.hidePanel(); }
      });
    });
  },

  showWelcome: function (offline) {
    const mins = Math.round(offline.sec / 60);
    const html = '<div class="welcome-stats">' +
      "Sen yokken fabrika çalışmaya devam etti! ⏱️ " + (mins >= 60 ? Math.floor(mins / 60) + " sa " + (mins % 60) + " dk" : mins + " dk") + "<br>" +
      "Üretilen oyuncak: <b>🧸 " + offline.products + "</b><br>" +
      "Kazanılan altın: <b>🪙 " + offline.coins + "</b><br>" +
      (offline.newPsycho > 0 ? "<b style='color:#c9302c'>⚠️ " + offline.newPsycho + " Luupie ilgisizlikten çıldırdı!</b>" : "Herkes seni özledi! 💖") +
      "</div>";
    UI._panel("🏭 Tekrar Hoş Geldin!", html);
  },
};
