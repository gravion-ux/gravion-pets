// petforge web — gallery & playground for the 849-pet catalogue.
// Data: pets.js (generated from src/petforge/data/catalogue.json).

import { PETS } from "./pets.js";

export const ORB_ANIMATIONS = [
  "blink", "ear-wiggle", "tail-wag", "orb-pulse", "float-bob",
  "sparkle-trail", "yawn", "hop", "twirl", "nod",
];

const COLOR_WORDS = {
  teal: "#2dd4bf", azure: "#38bdf8", blue: "#60a5fa", violet: "#a78bfa",
  purple: "#c084fc", pink: "#f472b6", rose: "#fb7185", red: "#f87171",
  crimson: "#ef4444", orange: "#fb923c", amber: "#fbbf24", gold: "#f59e0b",
  golden: "#f59e0b", yellow: "#fde047", green: "#4ade80", mint: "#6ee7b7",
  emerald: "#34d399", cyan: "#22d3ee", indigo: "#818cf8", lavender: "#c4b5fd",
  peach: "#fdba74", coral: "#fb7185", silver: "#cbd5e1", white: "#f8fafc",
  black: "#334155", brown: "#b45309", cream: "#fef3c7", sky: "#7dd3fc",
  magenta: "#e879f9", lime: "#a3e635", navy: "#3b82f6", plum: "#a21caf",
};

export function paletteColors(palette) {
  const words = String(palette || "").toLowerCase().split(/[^a-z]+/);
  const found = [];
  for (const w of words) {
    if (COLOR_WORDS[w] && !found.includes(COLOR_WORDS[w])) found.push(COLOR_WORDS[w]);
  }
  if (found.length === 0) return ["#5eead4", "#60a5fa"];
  if (found.length === 1) return [found[0], "#a78bfa"];
  return found.slice(0, 3);
}

export function faceStyle(face) {
  const f = String(face || "").toLowerCase();
  return {
    eyes: /sleepy|half|droop/.test(f) ? "sleepy"
      : /star/.test(f) ? "star"
      : /heart/.test(f) ? "heart"
      : /wink/.test(f) ? "wink"
      : /dot eyes|tiny eyes|small eyes|beady/.test(f) ? "dot" : "round",
    mouth: /grin|laugh|open/.test(f) ? "grin"
      : /smirk/.test(f) ? "smirk"
      : /fang/.test(f) ? "fang"
      : /flat|calm|serious/.test(f) ? "flat" : "smile",
    ears: /ear/.test(f),
    horns: /horn/.test(f),
  };
}

export function orbSvg(pet, size = 120) {
  const [c1, c2, c3] = paletteColors(pet.orb?.palette);
  const f = faceStyle(pet.orb?.face);
  const gid = "g-" + pet.id;
  const eye = (cx) => {
    if (f.eyes === "sleepy") return `<path d="M ${cx - 9} 58 Q ${cx} 64 ${cx + 9} 58" stroke="#0f172a" stroke-width="4" fill="none" stroke-linecap="round"/>`;
    if (f.eyes === "star") return `<path d="M ${cx} 48 l3.5 7 7.5 1 -5.5 5.5 1.5 7.5 -7 -3.5 -7 3.5 1.5 -7.5 -5.5 -5.5 7.5 -1 Z" fill="#0f172a"/>`;
    if (f.eyes === "heart") return `<path d="M ${cx} 64 C ${cx - 12} 54 ${cx - 6} 46 ${cx} 52 C ${cx + 6} 46 ${cx + 12} 54 ${cx} 64 Z" fill="#0f172a"/>`;
    if (f.eyes === "dot") return `<circle cx="${cx}" cy="56" r="3.5" fill="#0f172a"/>`;
    return `<circle cx="${cx}" cy="56" r="7" fill="#0f172a"/><circle cx="${cx + 2.5}" cy="53" r="2.4" fill="#fff"/>`;
  };
  const winkEye = `<path d="M 66 56 Q 75 61 84 56" stroke="#0f172a" stroke-width="4" fill="none" stroke-linecap="round"/>`;
  const mouth = {
    smile: `<path d="M 50 74 Q 60 83 70 74" stroke="#0f172a" stroke-width="4" fill="none" stroke-linecap="round"/>`,
    grin: `<path d="M 48 72 Q 60 86 72 72 Q 60 78 48 72 Z" fill="#0f172a"/>`,
    smirk: `<path d="M 52 76 Q 62 80 70 73" stroke="#0f172a" stroke-width="4" fill="none" stroke-linecap="round"/>`,
    fang: `<path d="M 50 73 Q 60 82 70 73" stroke="#0f172a" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M 55 77 l3 6 3 -6 Z" fill="#fff"/>`,
    flat: `<line x1="52" y1="76" x2="68" y2="76" stroke="#0f172a" stroke-width="4" stroke-linecap="round"/>`,
  }[f.mouth];
  const ears = f.ears ? `<g class="orb-ears"><path d="M 28 34 L 22 12 L 44 24 Z" fill="${c1}"/><path d="M 92 34 L 98 12 L 76 24 Z" fill="${c1}"/></g>` : "";
  const horns = f.horns ? `<path d="M 30 30 Q 24 14 34 10 Q 36 22 40 28 Z" fill="#f8fafc"/><path d="M 90 30 Q 96 14 86 10 Q 84 22 80 28 Z" fill="#f8fafc"/>` : "";
  return `<svg viewBox="0 0 120 120" width="${size}" height="${size}" role="img" aria-label="${pet.name} orb">
    <defs><radialGradient id="${gid}" cx="35%" cy="30%" r="80%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.85"/>
      <stop offset="35%" stop-color="${c1}"/>
      <stop offset="100%" stop-color="${c3 || c2}"/>
    </radialGradient></defs>
    ${ears}${horns}
    <circle cx="60" cy="62" r="46" fill="url(#${gid})"/>
    <ellipse cx="44" cy="40" rx="14" ry="8" fill="#ffffff" opacity="0.55"/>
    <g class="orb-eyes">${eye(45)}${f.eyes === "wink" ? winkEye : eye(75)}</g>
    ${mouth}
    <circle cx="34" cy="70" r="5" fill="#ffffff" opacity="0.35"/>
    <circle cx="86" cy="70" r="5" fill="#ffffff" opacity="0.35"/>
  </svg>`;
}

export function filterPets(pets, { category = "all", query = "" } = {}) {
  const q = query.trim().toLowerCase();
  return pets.filter((p) => {
    if (category !== "all" && p.category !== category) return false;
    if (!q) return true;
    const hay = [p.name, p.form, p.tagline, p.category, p.culture, p.form_type, ...(p.traits || [])].join(" ").toLowerCase();
    return hay.includes(q);
  });
}

export function categories(pets) {
  return [...new Set(pets.map((p) => p.category))].sort();
}

export function petAnimations(pet) {
  return ORB_ANIMATIONS.filter((a) => (pet.actions || []).includes(a));
}

// ---- UI (browser only) ----
if (typeof document !== "undefined") {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  let selected = PETS[0];

  function renderGrid() {
    const list = filterPets(PETS, { category: $("cat").value, query: $("search").value });
    $("count").textContent = `${list.length} of ${PETS.length} pets`;
    $("grid").innerHTML = list.map((p) => `
      <button class="pet-card ${p.id === selected.id ? "active" : ""}" data-id="${esc(p.id)}">
        <span class="orb-wrap">${orbSvg(p, 84)}</span>
        <span class="pet-name">${esc(p.name)}</span>
        <span class="pet-cat">${esc(p.category)}</span>
      </button>`).join("");
    for (const el of document.querySelectorAll(".pet-card")) {
      el.addEventListener("click", () => {
        selected = PETS.find((p) => p.id === el.dataset.id);
        renderGrid(); renderStage();
      });
    }
  }

  function renderStage() {
    const p = selected;
    const stat = (k, v) => `<div class="stat"><span>${k}</span><div class="bar"><i style="width:${v}%"></i></div><b>${v}</b></div>`;
    $("stage").innerHTML = `
      <div class="stage-orb" id="stage-orb">${orbSvg(p, 190)}
        <span class="sparkles" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
      </div>
      <h2>${esc(p.name)}</h2>
      <p class="tagline">${esc(p.tagline || "")}</p>
      <p class="muted">${esc(p.form)} · ${esc(p.category)}</p>
      <div class="stats">${Object.entries(p.base_stats).map(([k, v]) => stat(k, v)).join("")}</div>
      <p><strong>Signature move:</strong> ${esc(p.signature_move.name)} — ${esc(p.signature_move.description)}</p>
      <p class="muted"><strong>Loves:</strong> ${esc(p.favourite || "")}</p>
      <p class="muted"><strong>Quirks:</strong> ${esc((p.quirks || []).join(" · "))}</p>
      <div class="anim-row">
        ${petAnimations(p).map((a) => `<button data-anim="${a}">${a}</button>`).join("")}
        <button data-anim="signature" class="primary">✦ signature</button>
      </div>
      <p class="muted orb-note">Orb: ${esc(p.orb.palette)} · ${esc(p.orb.face)} · ${esc(p.orb.glow)}</p>`;
    for (const el of document.querySelectorAll("[data-anim]")) {
      el.addEventListener("click", () => {
        const orb = $("stage-orb");
        orb.className = "stage-orb";
        void orb.offsetWidth;
        orb.classList.add("anim-" + el.dataset.anim);
      });
    }
  }

  $("cat").innerHTML = `<option value="all">All categories</option>` +
    categories(PETS).map((c) => `<option value="${esc(c)}">${esc(c)}</option>`).join("");
  $("cat").addEventListener("change", renderGrid);
  $("search").addEventListener("input", renderGrid);
  renderGrid();
  renderStage();
}
