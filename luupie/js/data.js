/* Luupie — tür verileri, ekonomi ayarları */
"use strict";

const CONFIG = {
  designW: 480,
  designH: 854,
  maxPopulation: 10,
  // sevgi barı: 100 → 0 yaklaşık 6 saatte (saniyede düşüş)
  loveDecayPerSec: 100 / (6 * 3600),
  psychoThreshold: 25,
  sweetRecoverLove: 45,     // bu seviyeyi aşınca psycho → sweet
  graduationAgeSec: 48 * 3600,
  offlineCapSec: 4 * 3600,
  productEverySec: 20,      // sweet: 20 sn'de 1 ürün
  coinsPerProduct: 2,
  psychoProductMult: 2,     // kontrollü kaos: 2x üretim
  psychoContagionSec: 45,   // psycho'nun komşu sevgisini düşürme aralığı
  psychoContagionLove: 4,
  adoptBaseCost: 250,
  graduationBonus: 500,
  stationLockSec: 45,
  saveKey: "luupie_save_v1",
};

// tür sırası = seviye açılış sırası
const SPECIES = [
  { id: "bunny",   name: "Pofu",   unlockLevel: 1, personality: "Uykucu ama tatlı" },
  { id: "cat",     name: "Mırmır", unlockLevel: 1, personality: "Meraklı kaşif" },
  { id: "bear",    name: "Ponpon", unlockLevel: 1, personality: "Kocaman kalpli" },
  { id: "pig",     name: "Şefo",   unlockLevel: 2, personality: "Mutfağın kralı" },
  { id: "duck",    name: "Vako",   unlockLevel: 3, personality: "Ciddi işadamı" },
  { id: "robot",   name: "Cıvata", unlockLevel: 4, personality: "Kıvılcımlı zeka" },
  { id: "unicorn", name: "Uni",    unlockLevel: 5, personality: "Gökkuşağı ruhu" },
  { id: "punk",    name: "Çako",   unlockLevel: 6, personality: "Asi ama sevimli" },
  { id: "wolf",    name: "Rako",   unlockLevel: 7, personality: "Gizemli gececi" },
];

const FOODS = ["🍰", "🍪", "🧁", "🍭", "🍩", "🍎"];

const LEAGUE_RIVALS = [
  "Ayşe'nin Fabrikası", "PofuDukkan", "CrazyToys34", "MiniAtolye",
  "KaanOyuncak", "TatliCanavar", "ZeyZey Toys",
];

const NAME_POOL = [
  "Fıstık", "Badem", "Karamel", "Pamuk", "Zıpzıp", "Boncuk", "Şeker",
  "Fındık", "Lokum", "Peluş", "Gofret", "Vanilya", "Tarçın", "Kakao",
];

function speciesById(id) {
  return SPECIES.find(function (s) { return s.id === id; });
}
