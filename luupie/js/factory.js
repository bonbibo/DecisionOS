/* Luupie — izometrik fabrika içi renderer (tamamen prosedürel çizim) */
"use strict";

const Iso = {
  // halfW * (grid-1) * 2 = 480 → oda ekran genişliğini tam doldurur
  halfW: 40, halfH: 25,
  originX: 240, originY: 300,
  grid: 7,

  toScreen: function (i, j) {
    return {
      x: Iso.originX + (i - j) * Iso.halfW,
      y: Iso.originY + (i + j) * Iso.halfH,
    };
  },
};

const Factory = {
  staticLayer: null,   // önceden çizilmiş oda (duvar + zemin + sabit dekor)
  wallH: 205,
  conveyorBroken: false,

  // yürünebilir hücreler (makine/kutu olmayanlar)
  walkable: [],

  init: function () {
    Factory.walkable = [];
    for (let i = 0; i < Iso.grid; i++) {
      for (let j = 0; j < Iso.grid; j++) {
        // kenar şeritleri ve makine alanları kapalı
        const blocked =
          (i >= 5 && j <= 1) ||        // sağ arka: fırın
          (i >= 5 && j >= 2 && j <= 3) || // sağ orta: pres tezgahı
          (i <= 0 && j >= 4) ||        // solda kutu yığını
          (i >= 6 || j >= 6) ||        // ön kenarlar
          (i === 0 && j === 0);
        if (!blocked) Factory.walkable.push({ i: i, j: j });
      }
    }
    Factory._buildStatic();
  },

  randomCell: function () {
    return Factory.walkable[(Math.random() * Factory.walkable.length) | 0];
  },

  /* ---------- statik oda katmanı ---------- */
  _buildStatic: function () {
    const c = document.createElement("canvas");
    c.width = CONFIG.designW; c.height = CONFIG.designH;
    const g = c.getContext("2d");

    // arka fon (duvar arkası karanlık)
    const bgGrad = g.createLinearGradient(0, 0, 0, CONFIG.designH);
    bgGrad.addColorStop(0, "#241a26");
    bgGrad.addColorStop(0.5, "#33222b");
    bgGrad.addColorStop(1, "#1c1216");
    g.fillStyle = bgGrad;
    g.fillRect(0, 0, CONFIG.designW, CONFIG.designH);

    // odanın altına yumuşak gölge: diyamant kenarı boşlukta yüzmesin
    const front = Iso.toScreen(Iso.grid - 1, Iso.grid - 1);
    const ground = g.createRadialGradient(
      Iso.originX, front.y + 10, 20, Iso.originX, front.y + 10, 300);
    ground.addColorStop(0, "rgba(0,0,0,.45)");
    ground.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = ground;
    g.fillRect(0, front.y - 120, CONFIG.designW, 320);

    Factory._drawWalls(g);
    Factory._drawFloor(g);
    Factory._drawWallProps(g);
    Factory.staticLayer = c;
  },

  _drawWalls: function (g) {
    const top = Iso.toScreen(0, 0);
    const left = Iso.toScreen(0, Iso.grid - 1);
    const right = Iso.toScreen(Iso.grid - 1, 0);
    const H = Factory.wallH;

    // sol duvar (top-left yüzey)
    g.beginPath();
    g.moveTo(top.x, top.y - H);
    g.lineTo(left.x, left.y - H);
    g.lineTo(left.x, left.y);
    g.lineTo(top.x, top.y);
    g.closePath();
    const lw = g.createLinearGradient(left.x, 0, top.x, 0);
    lw.addColorStop(0, "#4a3040");
    lw.addColorStop(1, "#5d3c4a");
    g.fillStyle = lw; g.fill();

    // sağ duvar
    g.beginPath();
    g.moveTo(top.x, top.y - H);
    g.lineTo(right.x, right.y - H);
    g.lineTo(right.x, right.y);
    g.lineTo(top.x, top.y);
    g.closePath();
    const rw = g.createLinearGradient(top.x, 0, right.x, 0);
    rw.addColorStop(0, "#6b4655");
    rw.addColorStop(1, "#54323f");
    g.fillStyle = rw; g.fill();

    // duvar panel çizgileri
    g.strokeStyle = "rgba(0,0,0,.18)"; g.lineWidth = 2;
    for (let k = 1; k < 4; k++) {
      const yy = H * k / 4;
      g.beginPath();
      g.moveTo(left.x, left.y - yy);
      g.lineTo(top.x, top.y - yy);
      g.lineTo(right.x, right.y - yy);
      g.stroke();
    }

    // süpürgelik
    g.strokeStyle = "#2c1a22"; g.lineWidth = 4;
    g.beginPath();
    g.moveTo(left.x, left.y); g.lineTo(top.x, top.y); g.lineTo(right.x, right.y);
    g.stroke();

    // pencereler (sol duvarda 2 adet, iso paralelkenar)
    for (let w = 0; w < 2; w++) {
      Factory._isoWindow(g, top, left, 0.16 + w * 0.42, 0.36, H);
    }
    // sağ duvarda 1 pencere
    Factory._isoWindow(g, top, right, 0.14, 0.3, H);
  },

  // duvar yüzeyinde t0..t0+len arası pencere paralelkenarı
  _isoWindow: function (g, a, b, t0, len, H) {
    function lerp(p, q, t) { return { x: p.x + (q.x - p.x) * t, y: p.y + (q.y - p.y) * t }; }
    const p1 = lerp(a, b, t0), p2 = lerp(a, b, t0 + len);
    const yTop = -H * 0.78, yBot = -H * 0.34;
    g.beginPath();
    g.moveTo(p1.x, p1.y + yTop); g.lineTo(p2.x, p2.y + yTop);
    g.lineTo(p2.x, p2.y + yBot); g.lineTo(p1.x, p1.y + yBot);
    g.closePath();
    const sky = g.createLinearGradient(0, p1.y + yTop, 0, p1.y + yBot);
    sky.addColorStop(0, "#8fd3e8");
    sky.addColorStop(0.7, "#ffd9a0");
    sky.addColorStop(1, "#ff9d6e");
    g.fillStyle = sky; g.fill();
    // şehir silueti
    g.fillStyle = "rgba(80,50,90,.55)";
    const n = 5;
    for (let k = 0; k < n; k++) {
      const t = t0 + len * (k / n);
      const q1 = lerp(a, b, t), q2 = lerp(a, b, t + len / n * 0.8);
      const hgt = 12 + ((k * 37) % 20);
      g.beginPath();
      g.moveTo(q1.x, q1.y + yBot);
      g.lineTo(q1.x, q1.y + yBot - hgt);
      g.lineTo(q2.x, q2.y + yBot - hgt);
      g.lineTo(q2.x, q2.y + yBot);
      g.closePath(); g.fill();
    }
    // çerçeve
    g.strokeStyle = "#3a2430"; g.lineWidth = 5;
    g.stroke();
    // orta kayıt
    const m1 = lerp(p1, p2, 0.5);
    g.lineWidth = 3;
    g.beginPath(); g.moveTo(m1.x, m1.y + yTop); g.lineTo(m1.x, m1.y + yBot); g.stroke();
  },

  _drawFloor: function (g) {
    // ahşap zemin karoları
    for (let i = 0; i < Iso.grid; i++) {
      for (let j = 0; j < Iso.grid; j++) {
        const p = Iso.toScreen(i, j);
        const shade = ((i * 7 + j * 13) % 5) * 0.03;
        Factory._tile(g, p.x, p.y,
          "hsl(" + (28 - shade * 40) + ", " + (42 - shade * 30) + "%, " + (38 + shade * 22) + "%)");
      }
    }
    // orta halı (3×3, camgöbeği)
    for (let i = 2; i <= 4; i++) {
      for (let j = 2; j <= 4; j++) {
        const p = Iso.toScreen(i, j);
        Factory._tile(g, p.x, p.y, (i + j) % 2 ? "#2e6e63" : "#28615a", true);
      }
    }
  },

  _tile: function (g, x, y, color, isRug) {
    g.beginPath();
    g.moveTo(x, y);
    g.lineTo(x + Iso.halfW, y + Iso.halfH);
    g.lineTo(x, y + Iso.halfH * 2);
    g.lineTo(x - Iso.halfW, y + Iso.halfH);
    g.closePath();
    g.fillStyle = color; g.fill();
    g.strokeStyle = isRug ? "rgba(255,255,255,.06)" : "rgba(0,0,0,.22)";
    g.lineWidth = 1; g.stroke();
  },

  _drawWallProps: function (g) {
    const top = Iso.toScreen(0, 0);
    const left = Iso.toScreen(0, Iso.grid - 1);
    const right = Iso.toScreen(Iso.grid - 1, 0);
    const H = Factory.wallH;

    // "LUUPIE FABRİKASI" tabelası (sağ duvar üstü)
    function lerp(p, q, t) { return { x: p.x + (q.x - p.x) * t, y: p.y + (q.y - p.y) * t }; }
    const s1 = lerp(top, right, 0.5), s2 = lerp(top, right, 0.96);
    g.beginPath();
    g.moveTo(s1.x, s1.y - H * 0.92); g.lineTo(s2.x, s2.y - H * 0.92);
    g.lineTo(s2.x, s2.y - H * 0.68); g.lineTo(s1.x, s1.y - H * 0.68);
    g.closePath();
    g.fillStyle = "#6b4222"; g.fill();
    g.strokeStyle = "#c8934f"; g.lineWidth = 3; g.stroke();
    g.save();
    const mid = lerp(s1, s2, 0.5);
    const ang = Math.atan2(s2.y - s1.y, s2.x - s1.x);
    g.translate(mid.x, mid.y - H * 0.8);
    g.rotate(ang);
    g.fillStyle = "#ffe9c2";
    g.font = "900 13px Nunito, sans-serif";
    g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText("LUUPIE OYUNCAK", 0, 0);
    g.restore();

    // sol duvar dibinde yedek parça kutuları
    const binColors = ["#c94f4f", "#4f9ac9", "#67b357"];
    for (let k = 0; k < 3; k++) {
      const cell = Iso.toScreen(0.4, 1 + k * 1.1);
      Factory._bin(g, cell.x - 14, cell.y - 6, binColors[k]);
    }

    // ön-sol kutu yığını
    const b1 = Iso.toScreen(0.6, 5.4);
    Factory._box(g, b1.x, b1.y, 34);
    Factory._box(g, b1.x + 18, b1.y + 14, 30);
    Factory._box(g, b1.x + 4, b1.y - 18, 26);

    // "TEMİZ TUT!" tabelası ön sağda
    const sg = Iso.toScreen(6.1, 4.6);
    g.fillStyle = "#efe3c8";
    g.strokeStyle = "#6b4222"; g.lineWidth = 3;
    g.save();
    g.translate(sg.x, sg.y - 40);
    g.rotate(-0.08);
    g.beginPath();
    if (g.roundRect) g.roundRect(-38, -22, 76, 44, 6); else g.rect(-38, -22, 76, 44);
    g.fill(); g.stroke();
    g.fillStyle = "#6b4222";
    g.font = "900 11px Nunito, sans-serif";
    g.textAlign = "center";
    g.fillText("TEMİZ", 0, -5);
    g.fillText("TUT!", 0, 9);
    g.restore();
  },

  _bin: function (g, x, y, color) {
    g.fillStyle = color;
    g.strokeStyle = "rgba(0,0,0,.35)"; g.lineWidth = 2;
    g.beginPath();
    if (g.roundRect) g.roundRect(x - 16, y - 24, 32, 26, 4); else g.rect(x - 16, y - 24, 32, 26);
    g.fill(); g.stroke();
    // içindeki toplar
    for (let k = 0; k < 4; k++) {
      g.beginPath();
      g.arc(x - 9 + (k % 3) * 9, y - 24 - (k > 2 ? 6 : 2), 5, 0, 7);
      g.fillStyle = "hsl(" + ((k * 77) % 360) + ",60%,70%)";
      g.fill();
    }
  },

  _box: function (g, x, y, size) {
    const h = size * 0.5;
    // üst
    g.fillStyle = "#b98a54";
    g.beginPath();
    g.moveTo(x, y - h); g.lineTo(x + size / 2, y - h / 2);
    g.lineTo(x, y); g.lineTo(x - size / 2, y - h / 2);
    g.closePath(); g.fill();
    // sol
    g.fillStyle = "#8a6239";
    g.beginPath();
    g.moveTo(x - size / 2, y - h / 2); g.lineTo(x, y);
    g.lineTo(x, y + h); g.lineTo(x - size / 2, y);
    g.closePath(); g.fill();
    // sağ
    g.fillStyle = "#a1743f";
    g.beginPath();
    g.moveTo(x + size / 2, y - h / 2); g.lineTo(x, y);
    g.lineTo(x, y + h); g.lineTo(x + size / 2, y);
    g.closePath(); g.fill();
    g.strokeStyle = "rgba(0,0,0,.3)"; g.lineWidth = 1.5;
    g.strokeRect(x - 1, y - h / 2, 2, h);
  },

  /* ---------- her karede çizilen animasyonlu parçalar ---------- */
  drawAnimated: function (g, t) {
    Factory._drawConveyor(g, t);
    Factory._drawFurnace(g, t);
  },

  // arka duvara paralel yükseltilmiş konveyör bandı
  _drawConveyor: function (g, t) {
    const top = Iso.toScreen(0.2, 0.2);
    const left = Iso.toScreen(0.2, Iso.grid - 1.4);
    const lift = 78; // zeminden yükseklik
    function lerp(p, q, tt) { return { x: p.x + (q.x - p.x) * tt, y: p.y + (q.y - p.y) * tt }; }

    // bacaklar
    g.strokeStyle = "#3a2a30"; g.lineWidth = 5;
    for (let k = 0; k <= 2; k++) {
      const p = lerp(left, top, k / 2);
      g.beginPath(); g.moveTo(p.x, p.y - lift + 12); g.lineTo(p.x, p.y); g.stroke();
    }

    // bant gövdesi
    const bw = 22;
    g.beginPath();
    g.moveTo(left.x - bw / 2, left.y - lift);
    g.lineTo(top.x - bw / 2, top.y - lift);
    g.lineTo(top.x + bw / 2, top.y - lift + 6);
    g.lineTo(left.x + bw / 2, left.y - lift + 6);
    g.closePath();
    g.fillStyle = Factory.conveyorBroken ? "#5a4a4a" : "#4a4a5c";
    g.fill();
    g.strokeStyle = "#2a2a36"; g.lineWidth = 2; g.stroke();

    // hareketli şeritler
    const speed = Factory.conveyorBroken ? 0 : t * 0.06;
    g.strokeStyle = "rgba(255,255,255,.25)"; g.lineWidth = 2;
    for (let k = 0; k < 8; k++) {
      const tt = ((k / 8) + (speed % 1)) % 1;
      const p = lerp(left, top, tt);
      g.beginPath();
      g.moveTo(p.x - bw / 2, p.y - lift);
      g.lineTo(p.x + bw / 2, p.y - lift + 6);
      g.stroke();
    }

    // banttaki oyuncak kutuları
    if (!Factory.conveyorBroken) {
      const colors = ["#e85c5c", "#5ca9e8", "#7fd35c", "#e8b45c"];
      for (let k = 0; k < 4; k++) {
        const tt = ((k / 4) + (speed * 0.7 % 1)) % 1;
        const p = lerp(left, top, tt);
        g.fillStyle = colors[k];
        g.strokeStyle = "rgba(0,0,0,.3)"; g.lineWidth = 1.5;
        g.beginPath();
        if (g.roundRect) g.roundRect(p.x - 8, p.y - lift - 14, 16, 14, 3); else g.rect(p.x - 8, p.y - lift - 14, 16, 14);
        g.fill(); g.stroke();
      }
    } else {
      // arıza kıvılcımı
      const p = lerp(left, top, 0.5);
      if (Math.sin(t * 0.02) > 0) {
        g.fillStyle = "#ffd35c";
        for (let k = 0; k < 5; k++) {
          const a = t * 0.03 + k * 1.3;
          g.beginPath();
          g.arc(p.x + Math.cos(a) * 12, p.y - lift - 6 + Math.sin(a * 1.7) * 8, 2.2, 0, 7);
          g.fill();
        }
      }
      // uyarı işareti
      g.font = "22px sans-serif"; g.textAlign = "center";
      g.fillText("⚠️", p.x, p.y - lift - 22 + Math.sin(t * 0.005) * 3);
    }
  },

  // sağ köşede fırın + pres
  _drawFurnace: function (g, t) {
    const p = Iso.toScreen(5.6, 0.7);
    const glow = 0.55 + 0.45 * Math.sin(t * 0.004);

    // gövde
    g.fillStyle = "#7a4a3a";
    g.strokeStyle = "#3a2018"; g.lineWidth = 3;
    g.beginPath();
    if (g.roundRect) g.roundRect(p.x - 34, p.y - 92, 68, 86, 8); else g.rect(p.x - 34, p.y - 92, 68, 86);
    g.fill(); g.stroke();
    // kemer ağzı
    g.beginPath();
    g.moveTo(p.x - 22, p.y - 12);
    g.arc(p.x, p.y - 34, 22, Math.PI, 0);
    g.lineTo(p.x + 22, p.y - 12);
    g.closePath();
    const fg = g.createRadialGradient(p.x, p.y - 22, 4, p.x, p.y - 22, 26);
    fg.addColorStop(0, "rgba(255,220,120," + glow + ")");
    fg.addColorStop(1, "rgba(200,80,20," + glow * 0.8 + ")");
    g.fillStyle = fg; g.fill();
    g.stroke();
    // baca
    g.fillStyle = "#5c3a2e";
    g.fillRect(p.x + 10, p.y - 124, 16, 34);
    g.strokeRect(p.x + 10, p.y - 124, 16, 34);
    // duman
    g.fillStyle = "rgba(220,210,220,.16)";
    for (let k = 0; k < 3; k++) {
      const yy = ((t * 0.012 + k * 30) % 90);
      g.beginPath();
      g.arc(p.x + 18 + Math.sin((t * 0.002) + k) * 6, p.y - 128 - yy, 7 + yy * 0.12, 0, 7);
      g.fill();
    }

    // pres makinesi (piston animasyonu)
    const q = Iso.toScreen(5.7, 2.6);
    const stroke = Math.max(0, Math.sin(t * 0.005)) * 18;
    g.fillStyle = "#5c5c6e";
    g.strokeStyle = "#2a2a36";
    g.fillRect(q.x - 24, q.y - 78, 48, 16);
    g.strokeRect(q.x - 24, q.y - 78, 48, 16);
    g.fillStyle = "#8a8a9e";
    g.fillRect(q.x - 7, q.y - 62, 14, 22 + stroke);
    g.strokeRect(q.x - 7, q.y - 62, 14, 22 + stroke);
    g.fillStyle = "#4a4a5c";
    g.fillRect(q.x - 20, q.y - 40 + stroke, 40, 10);
    g.strokeRect(q.x - 20, q.y - 40 + stroke, 40, 10);
    // tezgah
    g.fillStyle = "#6e4a2e";
    g.fillRect(q.x - 26, q.y - 12, 52, 12);
    g.strokeRect(q.x - 26, q.y - 12, 52, 12);
  },

  // konveyör bandına dokunma testi (bant segmentine uzaklık)
  conveyorHit: function (x, y) {
    const a = Iso.toScreen(0.2, 0.2), b = Iso.toScreen(0.2, Iso.grid - 1.4);
    const lift = 78;
    const ax = a.x, ay = a.y - lift, bx = b.x, by = b.y - lift;
    const dx = bx - ax, dy = by - ay;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)));
    const px = ax + dx * t, py = ay + dy * t;
    return Math.hypot(x - px, y - py) < 34;
  },

  /* önde duran vinyet */
  drawVignette: function (g) {
    const grad = g.createRadialGradient(240, 400, 200, 240, 420, 460);
    grad.addColorStop(0, "rgba(0,0,0,0)");
    grad.addColorStop(1, "rgba(10,5,8,.55)");
    g.fillStyle = grad;
    g.fillRect(0, 0, CONFIG.designW, CONFIG.designH);
  },
};
