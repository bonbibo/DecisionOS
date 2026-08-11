/* Luupie — sprite yükleyici */
"use strict";

const Assets = {
  manifest: null,
  images: {},   // "bunny_sweet" -> Image

  load: function (onDone, onProgress) {
    fetch("assets/sprites/manifest.json")
      .then(function (r) { return r.json(); })
      .then(function (manifest) {
        Assets.manifest = manifest;
        const jobs = [];
        Object.keys(manifest).forEach(function (species) {
          Object.keys(manifest[species]).forEach(function (form) {
            jobs.push({ key: species + "_" + form, file: manifest[species][form].file });
          });
        });
        let loaded = 0;
        jobs.forEach(function (job) {
          const img = new Image();
          img.onload = img.onerror = function () {
            loaded++;
            if (onProgress) onProgress(loaded / jobs.length);
            if (loaded === jobs.length) onDone();
          };
          img.src = "assets/sprites/" + job.file;
          Assets.images[job.key] = img;
        });
      })
      .catch(function (err) {
        console.error("manifest yüklenemedi", err);
        alert("Sprite manifest'i yüklenemedi. Oyunu bir web sunucusundan açın (örn. python3 -m http.server).");
      });
  },

  sprite: function (species, form) {
    return Assets.images[species + "_" + form] || null;
  },

  spriteUrl: function (species, form) {
    const m = Assets.manifest && Assets.manifest[species] && Assets.manifest[species][form];
    return m ? "assets/sprites/" + m.file : "";
  },
};
