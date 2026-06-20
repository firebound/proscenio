// Unit tests for the UXP legacy-migration applier (api side; the pure
// planner is covered by legacy-migration.test.ts). Drives the document
// + the host mock's executeAsModal to preview and apply the
// underscore-prefix -> [ignore] rename batch.

import { afterEach, describe, expect, it } from "vitest";

import { app } from "photoshop";

import { applyUnderscoreMigration, previewUnderscoreMigration } from "../src/api/legacy-migration";

type MutableApp = { activeDocument: unknown };

function artLayer(name: string): Record<string, unknown> {
    return { name, visible: true, bounds: { left: 0, top: 0, right: 5, bottom: 5 } };
}

afterEach(() => {
    (app as MutableApp).activeDocument = null;
});

describe("previewUnderscoreMigration", () => {
    it("flags no document when none is open", () => {
        (app as MutableApp).activeDocument = null;
        expect(previewUnderscoreMigration()).toEqual({ candidates: [], noDocument: true });
    });

    it("lists underscore-prefixed layers as rename candidates", () => {
        (app as MutableApp).activeDocument = {
            name: "d.psd",
            width: 10,
            height: 10,
            layers: [artLayer("_temp"), artLayer("keep")],
        };
        const preview = previewUnderscoreMigration();
        expect(preview.noDocument).toBe(false);
        expect(preview.candidates).toHaveLength(1);
        expect(preview.candidates[0]?.newName).toBe("temp [ignore]");
    });
});

describe("applyUnderscoreMigration", () => {
    it("returns zero renames when no document is open", async () => {
        (app as MutableApp).activeDocument = null;
        expect(await applyUnderscoreMigration()).toEqual({ renamed: 0, failures: [] });
    });

    it("renames every underscore-prefixed layer inside the modal", async () => {
        const target = artLayer("_temp");
        (app as MutableApp).activeDocument = {
            name: "d.psd",
            width: 10,
            height: 10,
            layers: [target],
        };
        const result = await applyUnderscoreMigration();
        expect(result.renamed).toBe(1);
        expect(result.failures).toEqual([]);
        expect(target.name).toBe("temp [ignore]");
    });

    it("routes by id so a failed sibling does not steal the next sibling's rename", async () => {
        // Two same-named siblings: a name-only resolve would re-find the
        // first (whose rename just threw, so its name is unchanged) for the
        // second candidate too, leaving the real second sibling untouched.
        // Routing by the stable id renames the correct layer regardless.
        const locked = {
            id: 1,
            visible: true,
            bounds: { left: 0, top: 0, right: 5, bottom: 5 },
            _name: "_dup",
            get name(): string { return this._name; },
            set name(_v: string) { throw new Error("layer locked"); },
        };
        const sibling = { ...artLayer("_dup"), id: 2 };
        (app as MutableApp).activeDocument = {
            name: "d.psd",
            width: 10,
            height: 10,
            layers: [locked, sibling],
        };
        const result = await applyUnderscoreMigration();
        expect(result.renamed).toBe(1);
        expect(result.failures).toHaveLength(1);
        expect(sibling.name).toBe("dup [ignore]");
    });
});
