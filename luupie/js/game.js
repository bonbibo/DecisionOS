/* Luupie — oyun durumu, ekonomi, offline birikim, mezuniyet, lig, kayıt */
"use strict";

const Game = {
  state: null,
  ponchiqs: [],   // Ponchiq nesneleri
  floaters: [],   // uçan +para yazıları

  /* ---------- durum ---------- */
  newState: function () {
    return {
      coins: 120,
      products: 0,
      level: 1,
      xp: 0,
      graduates: [],          // {name, species, at}
      weekKey: Game._weekKey(),
      weekProducts: 0,
      rivals: null,           // lig rakip skorları
      lastSeen: Date.now(),
      nextId: 1,
    };
  },

  _weekKey: function () {
    const d = new Date();
    const onejan = new Date(d.getFullYear(), 0, 1);
    const week = Math.ceil((((d - onejan) / 86400000) + onejan.getDay() + 1) / 7);
    return d.getFullYear() + "-" + week;
  },

  xpNeeded: function () {
    return Math.round(100 * Math.pow(Game.state.level, 1.3));
  },

  addXP: function (n) {
    Game.state.xp += n;
    while (Game.state.xp >= Game.xpNeeded()) {
      Game.state.xp -= Game.xpNeeded();
      Game.state.level++;
      Sfx.coin();
      UI.toast("⭐ Seviye " + Game.state.level + "! Yeni türler açılmış olabilir.");
    }
    UI.refreshHud();
  },

  addCoins: function (n, byPonchiq) {
    Game.state.coins += n;
    if (byPonchiq) {
      const pos = byPonchiq.screenPos();
      Game.floaters.push({ x: pos.x, y: pos.y - 90, text: "+" + n + " 🪙", born: performance.now() });
    }
    UI.refreshHud();
  },

  addProducts: function (n) {
    Game.state.products += n;
    Game.state.weekProducts += n;
    UI.refreshHud();
  },

  /* ---------- nüfus ---------- */
  // her yeni slot bir öncekinin ~2 katı: 250, 500, 1000, ... (10. slot 32K)
  adoptCost: function () {
    return Math.round(CONFIG.adoptBaseCost * Math.pow(2, Math.max(0, Game.ponchiqs.length - 3)));
  },

  adopt: function (speciesId, silent) {
    if (Game.ponchiqs.length >= CONFIG.maxPopulation) {
      if (!silent) UI.toast("Fabrika dolu! (Maks " + CONFIG.maxPopulation + ")");
      return false;
    }
    const cost = silent ? 0 : Game.adoptCost();
    if (Game.state.coins < cost) {
      UI.toast("Yetersiz altın! (Gerekli: " + cost + ")");
      Sfx.bad();
      return false;
    }
    Game.state.coins -= cost;
    const name = NAME_POOL[(Math.random() * NAME_POOL.length) | 0] +
      (Game.state.nextId > NAME_POOL.length ? " " + Game.state.nextId : "");
    const p = new Ponchiq({
      id: Game.state.nextId++,
      species: speciesId,
      name: name,
      love: 90,
    });
    Game.ponchiqs.push(p);
    if (!silent) {
      Sfx.good();
      UI.toast(p.name + " fabrikaya katıldı! 🎉");
      Game.save();
    }
    UI.refreshHud();
    return true;
  },

  graduate: function (p) {
    Game.ponchiqs = Game.ponchiqs.filter(function (q) { return q !== p; });
    Game.state.graduates.push({ name: p.name, species: p.species, at: Date.now() });
    Game.state.coins += CONFIG.graduationBonus;
    UI.toast("🎓 " + p.name + " bir çocuk tarafından sahiplenildi! +" + CONFIG.graduationBonus + " 🪙");
    Sfx.coin();
    UI.refreshHud();
    Game.save();
  },

  /* ---------- lig ---------- */
  leagueTable: function () {
    const s = Game.state;
    // hafta değiştiyse sıfırla
    if (s.weekKey !== Game._weekKey()) {
      s.weekKey = Game._weekKey();
      s.weekProducts = 0;
      s.rivals = null;
    }
    if (!s.rivals) {
      s.rivals = LEAGUE_RIVALS.map(function (n) {
        return { name: n, base: 40 + Math.floor(Math.random() * 320) };
      });
    }
    // rakipler hafta içinde yavaşça ilerler
    const dayFrac = (Date.now() % (7 * 86400000)) / (7 * 86400000);
    const rows = s.rivals.map(function (r) {
      return { name: r.name, score: Math.floor(r.base * (0.3 + dayFrac * 3)), me: false };
    });
    rows.push({ name: "Senin Fabrikan", score: s.weekProducts, me: true });
    rows.sort(function (x, y) { return y.score - x.score; });
    return rows;
  },

  /* ---------- offline birikim ---------- */
  applyOffline: function () {
    const elapsed = Math.max(0, (Date.now() - Game.state.lastSeen) / 1000);
    if (elapsed < 90) return null; // kısa aradan sayılmaz

    const sec = Math.min(elapsed, CONFIG.offlineCapSec);
    let products = 0, newPsycho = 0;

    Game.ponchiqs.forEach(function (p) {
      // düşük hızda üretim (%60 verim)
      const mult = p.form === "psycho" ? CONFIG.psychoProductMult : 1;
      products += Math.floor(sec / CONFIG.productEverySec * 0.6 * mult);
      // sevgi de düşer ama 12'nin altına inmez (dönüş cezası yumuşak)
      const before = p.form;
      p.love = Math.max(12, p.love - CONFIG.loveDecayPerSec * elapsed);
      if (p.love < CONFIG.psychoThreshold && p.form === "sweet") {
        p.form = "psycho";
      }
      if (before === "sweet" && p.form === "psycho") newPsycho++;
    });

    const coins = products * CONFIG.coinsPerProduct;
    Game.state.products += products;
    Game.state.weekProducts += products;
    Game.state.coins += coins;
    return { sec: sec, products: products, coins: coins, newPsycho: newPsycho };
  },

  /* ---------- güncelleme ---------- */
  update: function (dt) {
    Game.ponchiqs.forEach(function (p) { p.update(dt, Game); });

    // mezuniyet kontrolü
    const grads = Game.ponchiqs.filter(function (p) {
      return p.ageSec() >= CONFIG.graduationAgeSec;
    });
    grads.forEach(function (p) { Game.graduate(p); });

    // uçan yazılar
    const now = performance.now();
    Game.floaters = Game.floaters.filter(function (f) { return now - f.born < 1400; });
  },

  drawFloaters: function (g) {
    const now = performance.now();
    Game.floaters.forEach(function (f) {
      const t = (now - f.born) / 1400;
      g.globalAlpha = 1 - t;
      g.font = "900 14px Nunito, sans-serif";
      g.textAlign = "center";
      g.fillStyle = "#ffd35c";
      g.strokeStyle = "rgba(0,0,0,.6)";
      g.lineWidth = 3;
      g.strokeText(f.text, f.x, f.y - t * 34);
      g.fillText(f.text, f.x, f.y - t * 34);
      g.globalAlpha = 1;
    });
  },

  /* ---------- kayıt ---------- */
  save: function () {
    Game.state.lastSeen = Date.now();
    const data = {
      state: Game.state,
      ponchiqs: Game.ponchiqs.map(function (p) { return p.serialize(); }),
      conveyorBroken: Factory.conveyorBroken,
    };
    try { localStorage.setItem(CONFIG.saveKey, JSON.stringify(data)); }
    catch (e) { /* gizli mod vb. */ }
  },

  load: function () {
    let data = null;
    try { data = JSON.parse(localStorage.getItem(CONFIG.saveKey)); }
    catch (e) { data = null; }

    if (data && data.state) {
      Game.state = Object.assign(Game.newState(), data.state);
      Game.ponchiqs = (data.ponchiqs || []).map(function (d) { return new Ponchiq(d); });
      Factory.conveyorBroken = !!data.conveyorBroken;
      return true;
    }
    return false;
  },

  /* ---------- yeni oyun ---------- */
  freshStart: function () {
    Game.state = Game.newState();
    Game.ponchiqs = [];
    Game.adopt("bunny", true);
    Game.adopt("cat", true);
    Game.adopt("bear", true);
    // ilk dakikalarda Toy Trouble tanıtımı için biri sinirli başlar
    if (Game.ponchiqs[2]) Game.ponchiqs[2].love = 27;
    Game.save();
  },
};
