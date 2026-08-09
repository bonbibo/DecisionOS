/* Luupie — karakter varlığı: yürüme, sprite animasyonu, sevgi/psycho durumu */
"use strict";

function Ponchiq(data) {
  this.id = data.id;
  this.species = data.species;
  this.name = data.name;
  this.love = data.love != null ? data.love : 90;
  this.bornAt = data.bornAt || Date.now();
  this.form = data.form || "sweet";      // "sweet" | "psycho"
  this.lockedUntil = data.lockedUntil || 0; // zapt istasyonu kilidi (ms epoch)

  // dünya konumu (iso hücre koordinatı, float)
  const cell = Factory.randomCell();
  this.fi = cell.i; this.fj = cell.j;
  this.target = null;
  this.speed = 0.55 + Math.random() * 0.25;  // hücre/sn
  this.facing = 1;                            // 1: sağa bakar, -1 ayna
  this.idleUntil = 0;
  this.phase = Math.random() * 10;            // animasyon fazı
  this.emote = null;                          // {icon, until}
  this.produceTimer = Math.random() * CONFIG.productEverySec;
  this.contagionTimer = CONFIG.psychoContagionSec;
}

Ponchiq.prototype.ageSec = function () {
  return (Date.now() - this.bornAt) / 1000;
};

Ponchiq.prototype.isLocked = function () {
  return Date.now() < this.lockedUntil;
};

Ponchiq.prototype.serialize = function () {
  return {
    id: this.id, species: this.species, name: this.name,
    love: this.love, bornAt: this.bornAt, form: this.form,
    lockedUntil: this.lockedUntil,
  };
};

Ponchiq.prototype.update = function (dt, game) {
  // sevgi düşüşü
  this.love = Math.max(0, this.love - CONFIG.loveDecayPerSec * dt);

  // psycho dönüşümü
  if (this.form === "sweet" && this.love < CONFIG.psychoThreshold) {
    this.form = "psycho";
    this.emote = { icon: "💢", until: performance.now() + 4000 };
    Sfx.psycho();
    UI.toast(this.name + " çıldırdı! Üzerine dokunup zapt et!");
  }
  if (this.form === "psycho" && this.love >= CONFIG.sweetRecoverLove) {
    this.form = "sweet";
    this.emote = { icon: "💖", until: performance.now() + 4000 };
    UI.toast(this.name + " sakinleşti!");
  }

  // üretim
  this.produceTimer -= dt;
  if (this.produceTimer <= 0) {
    this.produceTimer = CONFIG.productEverySec;
    const mult = this.form === "psycho" ? CONFIG.psychoProductMult : 1;
    const broken = Factory.conveyorBroken ? 0.5 : 1;
    const products = Math.round(1 * mult * broken) || 0;
    if (products > 0) {
      game.addProducts(products);
      game.addCoins(products * CONFIG.coinsPerProduct, this);
    }
  }

  // psycho bulaşması: yakındaki bir arkadaşın sevgisini düşürür
  if (this.form === "psycho") {
    this.contagionTimer -= dt;
    if (this.contagionTimer <= 0) {
      this.contagionTimer = CONFIG.psychoContagionSec;
      const others = game.ponchiqs.filter(function (p) { return p !== this && p.form === "sweet"; }, this);
      const victim = others.length ? others[(Math.random() * others.length) | 0] : null;
      if (victim) {
        victim.love = Math.max(0, victim.love - CONFIG.psychoContagionLove);
        victim.emote = { icon: "😟", until: performance.now() + 2500 };
      }
    }
  }

  // dolaşma
  const now = performance.now();
  if (!this.target && now > this.idleUntil) {
    const cell = Factory.randomCell();
    this.target = { i: cell.i, j: cell.j };
  }
  if (this.target) {
    const di = this.target.i - this.fi, dj = this.target.j - this.fj;
    const dist = Math.hypot(di, dj);
    const spd = this.form === "psycho" ? this.speed * 1.9 : this.speed;
    if (dist < 0.05) {
      this.fi = this.target.i; this.fj = this.target.j;
      this.target = null;
      this.idleUntil = now + 1200 + Math.random() * 3500;
    } else {
      const step = Math.min(dist, spd * dt);
      this.fi += di / dist * step;
      this.fj += dj / dist * step;
      // ekran yönüne göre bak: iso'da x = (i - j)
      const sx = (di - dj);
      if (Math.abs(sx) > 0.05) this.facing = sx > 0 ? 1 : -1;
    }
  }
};

Ponchiq.prototype.screenPos = function () {
  const p = Iso.toScreen(this.fi, this.fj);
  return { x: p.x, y: p.y + Iso.halfH }; // ayak noktası karo ortası
};

Ponchiq.prototype.draw = function (g, t) {
  const img = Assets.sprite(this.species, this.form);
  if (!img || !img.complete || !img.naturalWidth) return;

  const pos = this.screenPos();
  const targetH = this.form === "psycho" ? 100 : 92;
  const scale = targetH / img.naturalHeight;
  const w = img.naturalWidth * scale, h = targetH;

  const walking = !!this.target;
  const tt = t * 0.001 + this.phase;
  const bob = walking ? Math.abs(Math.sin(tt * 9)) * 5 : Math.sin(tt * 2) * 1.6;
  const rock = walking ? Math.sin(tt * 9) * 0.07 : Math.sin(tt * 1.3) * 0.02;
  const shake = this.form === "psycho" ? Math.sin(tt * 31) * 1.8 : 0;

  // gölge
  g.beginPath();
  g.ellipse(pos.x, pos.y + 2, w * 0.32, 7, 0, 0, 7);
  g.fillStyle = "rgba(0,0,0,.30)";
  g.fill();

  // psycho aurası
  if (this.form === "psycho") {
    const glow = 0.25 + 0.15 * Math.sin(tt * 8);
    const rg = g.createRadialGradient(pos.x, pos.y - h / 2, 6, pos.x, pos.y - h / 2, h * 0.75);
    rg.addColorStop(0, "rgba(255,60,40," + glow + ")");
    rg.addColorStop(1, "rgba(255,60,40,0)");
    g.fillStyle = rg;
    g.beginPath(); g.arc(pos.x, pos.y - h / 2, h * 0.75, 0, 7); g.fill();
  }

  g.save();
  g.translate(pos.x + shake, pos.y - bob);
  g.rotate(rock);
  g.scale(this.facing, 1);
  // yürürken hafif squash & stretch
  const sq = walking ? 1 + Math.sin(tt * 18) * 0.03 : 1;
  g.scale(1 / sq, sq);
  g.drawImage(img, -w / 2, -h, w, h);
  g.restore();

  // kilit göstergesi
  if (this.isLocked()) {
    g.font = "16px sans-serif"; g.textAlign = "center";
    g.fillText("🔒", pos.x + w * 0.32, pos.y - h - 4);
  }

  // sevgi barı (düşükse göster)
  if (this.love < 60 && this.form === "sweet") {
    const bw = 40;
    g.fillStyle = "rgba(0,0,0,.5)";
    g.fillRect(pos.x - bw / 2, pos.y - h - 12, bw, 6);
    g.fillStyle = this.love < CONFIG.psychoThreshold + 10 ? "#ff5e5e" : "#ff9dc0";
    g.fillRect(pos.x - bw / 2 + 1, pos.y - h - 11, (bw - 2) * this.love / 100, 4);
  }

  // emote balonu
  if (this.emote && performance.now() < this.emote.until) {
    const by = pos.y - h - 26 + Math.sin(tt * 4) * 2;
    g.beginPath();
    g.arc(pos.x, by, 14, 0, 7);
    g.fillStyle = "rgba(255,250,240,.95)";
    g.fill();
    g.strokeStyle = "#a97346"; g.lineWidth = 2; g.stroke();
    g.font = "15px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText(this.emote.icon, pos.x, by + 1);
    g.textBaseline = "alphabetic";
  } else if (this.form === "psycho") {
    g.font = "18px sans-serif"; g.textAlign = "center";
    g.fillText("💢", pos.x - w * 0.35, pos.y - h + Math.sin(tt * 12) * 3);
  }
};

// dokunma testi (stage koordinatı)
Ponchiq.prototype.hitTest = function (x, y) {
  const pos = this.screenPos();
  const h = 92, w = 70;
  return x > pos.x - w / 2 && x < pos.x + w / 2 && y > pos.y - h - 10 && y < pos.y + 8;
};
