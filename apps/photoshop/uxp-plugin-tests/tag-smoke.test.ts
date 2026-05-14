// SPEC 011 v1 tag-taxonomy parity oracle. One synthetic layer tree
// exercises every bracket tag the planner is supposed to honour; the
// emitted manifest is asserted tag-by-tag AND snapshot-diffed against
// the committed golden at
// `examples/generated/psd_to_blender/tag_smoke/tag_smoke.expected.json`.
//
// Why a separate test file and not just one more `describe` in
// `exporter.test.ts`: this is the **regression baseline** for the v1
// taxonomy. The other suite covers individual tags in isolation;
// `tag_smoke` answers "does the planner still emit the same thing
// when every tag is present in the same tree at once?". The golden
// catches drift the per-tag tests miss (ordering, anchor handling,
// nested-merge collapse).
//
// Regenerate the golden with `pnpm run test -- --update tag-smoke`.

import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { buildExportPlan, buildManifest } from "../src/domain/planner";
import type { ArtLayer, Layer, LayerSet } from "../src/domain/layer";
import type { PolygonEntry, SpriteFrameEntry } from "../src/domain/manifest";

const GOLDEN_PATH = resolve(
    __dirname,
    "../../../examples/generated/psd_to_blender/tag_smoke/tag_smoke.expected.json",
);

function art(name: string, bounds: ArtLayer["bounds"], visible = true): ArtLayer {
    return { kind: "art", name, visible, bounds };
}

function set(name: string, layers: Layer[], visible = true): LayerSet {
    return { kind: "set", name, visible, layers };
}

// Synthetic tree mirroring `examples/authored/doll/02_photoshop_setup/
// doll_tagged.psd` at miniature scale (10x10 bboxes) so the test math
// stays human-readable.
function buildSmokeTree(): Layer[] {
    return [
        // [ignore] - excluded entirely
        art("ignored_layer [ignore]", { x: 0, y: 0, w: 8, h: 8 }),

        // [merge] - flattens children into one polygon entry
        set("hair [merge]", [
            art("hair_front", { x: 10, y: 10, w: 8, h: 8 }),
            art("hair_back", { x: 12, y: 12, w: 8, h: 8 }),
        ]),

        // Nested [merge] inside [merge] - inner collapses into outer
        set("outer [merge]", [
            art("outer_art", { x: 30, y: 30, w: 8, h: 8 }),
            set("inner [merge]", [
                art("inner_art_a", { x: 34, y: 30, w: 8, h: 8 }),
                art("inner_art_b", { x: 38, y: 30, w: 8, h: 8 }),
            ]),
        ]),

        // [folder:NAME] cascade + [polygon] explicit + [mesh] + [blend:*]
        set("body [folder:body]", [
            art("torso [polygon]", { x: 50, y: 50, w: 16, h: 32 }),
            art("chest [mesh]", { x: 50, y: 50, w: 16, h: 32 }),
            art("chest_mult [mesh] [blend:multiply]", { x: 50, y: 50, w: 16, h: 32 }),
        ]),

        // [folder:NAME] + [origin:X,Y] + [scale:N] + [path:NAME]
        set("teste [folder:teste]", [
            art("arm [origin:10,20] [scale:2.0] [path:weapon]", { x: 70, y: 0, w: 12, h: 20 }),
        ]),

        // [spritesheet] with [origin] marker child + frames as [merge] groups
        set("eyes [spritesheet]", [
            set("0 [merge]", [
                art("eye_L_open", { x: 100, y: 30, w: 8, h: 4 }),
                art("eye_R_open", { x: 90, y: 30, w: 8, h: 4 }),
            ]),
            set("1 [merge]", [
                art("eye_L_closed", { x: 100, y: 30, w: 8, h: 4 }),
                art("eye_R_closed", { x: 90, y: 30, w: 8, h: 4 }),
            ]),
            art("pivot [origin]", { x: 99, y: 32, w: 2, h: 2 }),
        ]),

        // Per-layer [blend:screen] and [blend:additive]
        art("eye_L_scrn [blend:screen]", { x: 100, y: 30, w: 8, h: 4 }),
        art("eye_R_add [blend:additive]", { x: 90, y: 30, w: 8, h: 4 }),

        // [name:pre*suf] - planner accepts, does not rewrite descendants in v1
        set("hands [name:lh_*]", [
            art("hand_L", { x: 200, y: 100, w: 10, h: 12 }),
            art("hand_R", { x: 180, y: 100, w: 10, h: 12 }),
        ]),
    ];
}

const DOC = { name: "tag_smoke.psd", width: 256, height: 256 };
const OPTS = { skipHidden: true };

describe("tag_smoke - per-tag assertions", () => {
    const m = buildManifest(DOC, buildSmokeTree(), OPTS);

    it("emits format_version 2", () => {
        expect(m.format_version).toBe(2);
    });

    it("[ignore] excludes the layer from the manifest", () => {
        expect(m.layers.find((L) => L.name === "ignored_layer")).toBeUndefined();
    });

    it("[merge] flattens descendants into one polygon entry", () => {
        const hair = m.layers.find((L) => L.name === "hair");
        expect(hair?.kind).toBe("polygon");
    });

    it("nested [merge] inside [merge] collapses into a single entry", () => {
        const outer = m.layers.filter((L) => L.name === "outer");
        expect(outer).toHaveLength(1);
        expect(outer[0]?.kind).toBe("polygon");
        // The inner [merge] group should NOT surface its own entry.
        expect(m.layers.find((L) => L.name === "inner")).toBeUndefined();
    });

    it("[folder:NAME] cascades subfolder onto descendants + joins the name", () => {
        // joinName prefixes the parent group name; subfolder reflects the tag value.
        const torso = m.layers.find((L) => L.name === "body__torso") as PolygonEntry | undefined;
        expect(torso?.subfolder).toBe("body");
        const arm = m.layers.find((L) => L.name === "teste__arm") as PolygonEntry | undefined;
        expect(arm?.subfolder).toBe("teste");
    });

    it("[mesh] sets kind to mesh, [polygon] explicit stays polygon", () => {
        expect(m.layers.find((L) => L.name === "body__chest")?.kind).toBe("mesh");
        expect(m.layers.find((L) => L.name === "body__chest_mult")?.kind).toBe("mesh");
        expect(m.layers.find((L) => L.name === "body__torso")?.kind).toBe("polygon");
    });

    it("[blend:*] sets blend_mode on the right entries", () => {
        expect(m.layers.find((L) => L.name === "body__chest_mult")?.blend_mode).toBe("multiply");
        expect(m.layers.find((L) => L.name === "eye_L_scrn")?.blend_mode).toBe("screen");
        expect(m.layers.find((L) => L.name === "eye_R_add")?.blend_mode).toBe("additive");
    });

    it("[origin:X,Y] writes the origin field", () => {
        const arm = m.layers.find((L) => L.name === "teste__arm") as PolygonEntry | undefined;
        expect(arm?.origin).toEqual([10, 20]);
    });

    it("[scale:N] multiplies bbox dimensions", () => {
        const arm = m.layers.find((L) => L.name === "teste__arm") as PolygonEntry | undefined;
        // Source bbox was 12x20 at scale 2.0 -> 24x40.
        expect(arm?.size).toEqual([24, 40]);
    });

    it("[path:NAME] overrides the filename leaf", () => {
        const arm = m.layers.find((L) => L.name === "teste__arm") as PolygonEntry | undefined;
        expect(arm?.path).toBe("images/teste/weapon.png");
    });

    it("[spritesheet] emits one sprite_frame entry with frames + marker origin", () => {
        const eyes = m.layers.find((L) => L.name === "eyes") as SpriteFrameEntry | undefined;
        expect(eyes?.kind).toBe("sprite_frame");
        expect(eyes?.frames.map((f) => f.index)).toEqual([0, 1]);
        // pivot marker centre = (99 + 2/2, 32 + 2/2) = (100, 33).
        expect(eyes?.origin).toEqual([100, 33]);
    });

    it("[name:pre*suf] passes through (planner does not rewrite in v1)", () => {
        // The hands group is a name-template carrier; children cascade their
        // raw names via joinName (`hands__hand_L`). The literal `lh_*` rewrite
        // is deferred to the v2 planner (see specs/backlog.md).
        const handL = m.layers.find((L) => L.name === "hands__hand_L");
        expect(handL).toBeDefined();
    });
});

describe("tag_smoke - plan warnings", () => {
    const plan = buildExportPlan(DOC, buildSmokeTree(), OPTS);

    it("flags [scale:2.0] as scale-subpixel only when the math demands it", () => {
        // 12x20 * 2.0 = 24x40 (integer). No warning expected.
        const subpixel = plan.warnings.filter((w) => w.code === "scale-subpixel");
        expect(subpixel).toHaveLength(0);
    });

    it("does not flag the nested [merge] as sprite-frame-malformed", () => {
        const malformed = plan.warnings.filter((w) => w.code === "sprite-frame-malformed");
        expect(malformed).toHaveLength(0);
    });
});

describe("tag_smoke - golden snapshot", () => {
    it("emitted manifest matches the committed golden", async () => {
        const m = buildManifest(DOC, buildSmokeTree(), OPTS);
        // `toMatchFileSnapshot` writes the file on first run / when
        // --update is passed; afterwards it byte-diffs.
        await expect(JSON.stringify(m, null, 2) + "\n").toMatchFileSnapshot(GOLDEN_PATH);
    });
});

// Re-export for ad-hoc debugging via `pnpm vitest --reporter=verbose tag-smoke`.
export { buildSmokeTree };
