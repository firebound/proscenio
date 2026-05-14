// SPEC 011 Wave 11.6: `_<name>` -> `[ignore]` rename planner.

import { describe, expect, it } from "vitest";

import type { ArtLayer, Layer, LayerSet } from "../src/domain/layer";
import { planUnderscoreMigration } from "../src/domain/legacy-migration";

function art(name: string): ArtLayer {
    return { kind: "art", name, visible: true, bounds: { x: 0, y: 0, w: 10, h: 10 } };
}

function set(name: string, layers: Layer[]): LayerSet {
    return { kind: "set", name, visible: true, layers };
}

describe("planUnderscoreMigration", () => {
    it("renames a leading-underscore layer to `<name> [ignore]`", () => {
        const candidates = planUnderscoreMigration([art("_torso")]);
        expect(candidates).toEqual([
            { layerPath: ["_torso"], oldName: "_torso", newName: "torso [ignore]" },
        ]);
    });

    it("strips all leading underscores", () => {
        const candidates = planUnderscoreMigration([art("__shadow")]);
        expect(candidates[0].newName).toBe("shadow [ignore]");
    });

    it("does not re-add [ignore] when already present", () => {
        const candidates = planUnderscoreMigration([art("_done [ignore]")]);
        expect(candidates[0].newName).toBe("done [ignore]");
    });

    it("converts a bare `_` into `[ignore]`", () => {
        const candidates = planUnderscoreMigration([art("_")]);
        expect(candidates[0].newName).toBe("[ignore]");
    });

    it("skips layers without a leading underscore", () => {
        const candidates = planUnderscoreMigration([art("torso"), art("head")]);
        expect(candidates).toEqual([]);
    });

    it("recurses into groups, preserving full layer path", () => {
        const layers: Layer[] = [
            set("body", [
                art("_helper"),
                set("_archived", [art("_old")]),
            ]),
        ];
        const candidates = planUnderscoreMigration(layers);
        expect(candidates).toHaveLength(3);
        expect(candidates[0]).toEqual({
            layerPath: ["body", "_helper"],
            oldName: "_helper",
            newName: "helper [ignore]",
        });
        expect(candidates[1].layerPath).toEqual(["body", "_archived"]);
        expect(candidates[2].layerPath).toEqual(["body", "_archived", "_old"]);
    });

    it("drops the leading `_` when the stripped name already carries [ignore]", () => {
        // `_[ignore]` strips to `[ignore]`; the migration normalises
        // the cosmetic underscore prefix even though the semantic
        // (the [ignore] tag) is already present in both forms.
        const candidates = planUnderscoreMigration([art("_[ignore]")]);
        expect(candidates).toHaveLength(1);
        expect(candidates[0].oldName).toBe("_[ignore]");
        expect(candidates[0].newName).toBe("[ignore]");
    });
});
