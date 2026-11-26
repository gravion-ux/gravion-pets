import { test } from "node:test";
import assert from "node:assert/strict";
import { PETS } from "../pets.js";
import {
  paletteColors, faceStyle, orbSvg, filterPets, categories, petAnimations, ORB_ANIMATIONS,
} from "../app.js";

test("catalogue carries 800+ pets, each with an orb spec", () => {
  assert.ok(PETS.length >= 800, `only ${PETS.length} pets`);
  for (const p of PETS) {
    assert.ok(p.orb?.palette, p.id);
    assert.ok(p.orb?.face, p.id);
    assert.ok(p.signature_move?.name, p.id);
    assert.ok(p.culture, p.id);
    assert.ok(p.form_type, p.id);
    assert.ok(p.evolution?.stage3_xp > p.evolution?.stage2_xp, p.id);
  }
});

test("search finds pets by culture", () => {
  const greek = filterPets(PETS, { query: "greek" });
  assert.ok(greek.length >= 40);
  assert.ok(greek.every((p) => p.culture === "greek"));
});

test("palette parsing finds gradient colours", () => {
  assert.deepEqual(paletteColors("teal-to-azure gradient"), ["#2dd4bf", "#38bdf8"]);
  assert.equal(paletteColors("mystery").length, 2);
});

test("face style picks eye and mouth variants", () => {
  assert.equal(faceStyle("round glossy eyes and a tiny smile").eyes, "round");
  assert.equal(faceStyle("sleepy half-closed eyes").eyes, "sleepy");
  assert.equal(faceStyle("big grin with fangs").mouth, "grin");
});

test("orbSvg renders gradient, eyes and mouth", () => {
  const svg = orbSvg(PETS[0]);
  assert.ok(svg.includes("<svg"));
  assert.ok(svg.includes("radialGradient"));
  assert.ok(svg.includes("orb-eyes"));
});

test("filterPets honours category and search", () => {
  const cats = categories(PETS);
  assert.ok(cats.includes("anime"));
  const anime = filterPets(PETS, { category: "anime" });
  assert.ok(anime.length > 0 && anime.every((p) => p.category === "anime"));
  const found = filterPets(PETS, { query: PETS[0].name });
  assert.ok(found.some((p) => p.id === PETS[0].id));
  assert.equal(filterPets(PETS, { query: "zzz-no-match" }).length, 0);
});

test("every pet can perform all ten orb animations", () => {
  for (const p of PETS) assert.deepEqual(petAnimations(p), ORB_ANIMATIONS, p.id);
});
