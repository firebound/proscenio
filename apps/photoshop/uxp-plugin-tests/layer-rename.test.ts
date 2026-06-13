// Unit tests for the layer-rename api. Drives app.activeDocument + the
// host mock's core.executeAsModal (which runs its callback inline), so
// the rename mutation and its error handling are exercised end-to-end.

import { afterEach, describe, expect, it, vi } from "vitest";

import { app, core } from "photoshop";

import { renameLayer } from "../src/api/layer-rename";

type MutableApp = { activeDocument: unknown };

afterEach(() => {
    (app as MutableApp).activeDocument = null;
    vi.restoreAllMocks();
});

describe("renameLayer", () => {
    it("fails when no document is open", async () => {
        (app as MutableApp).activeDocument = null;
        expect(await renameLayer(["a"], "b")).toEqual({ ok: false, reason: "no active document" });
    });

    it("fails when the layer path does not resolve", async () => {
        (app as MutableApp).activeDocument = { layers: [{ name: "other" }] };
        expect(await renameLayer(["missing"], "x")).toEqual({ ok: false, reason: "layer not found" });
    });

    it("renames the resolved layer inside the modal", async () => {
        const target = { name: "torso", xmpMetadata: "" };
        (app as MutableApp).activeDocument = { layers: [target] };
        const result = await renameLayer(["torso"], "torso [mesh]");
        expect(result).toEqual({ ok: true });
        expect(target.name).toBe("torso [mesh]");
    });

    it("resolves by id when the cached name-path is stale (renamed parent group)", async () => {
        // The doll_tagged.psd failure: the tree cached ["Agrupar 1","eye.R"]
        // but the group was renamed to "eyes", so the name-path missed at
        // depth 0. The stable id still finds the layer.
        const target = { name: "eye.R", id: 99, xmpMetadata: "" };
        (app as MutableApp).activeDocument = { layers: [{ name: "eyes", id: 5, layers: [target] }] };
        const result = await renameLayer(["Agrupar 1", "eye.R"], "eye.R [folder:eyes]", 99);
        expect(result).toEqual({ ok: true });
        expect(target.name).toBe("eye.R [folder:eyes]");
    });

    it("falls back to the name-path when no id is given", async () => {
        const target = { name: "torso", xmpMetadata: "" };
        (app as MutableApp).activeDocument = { layers: [target] };
        expect(await renameLayer(["torso"], "torso [mesh]")).toEqual({ ok: true });
        expect(target.name).toBe("torso [mesh]");
    });

    it("prefers the id even when a different layer matches the stale name-path", async () => {
        // Two layers share the cached leaf name; the id disambiguates to
        // the intended one instead of the first name match.
        const intended = { name: "dup", id: 99, xmpMetadata: "" };
        const decoy = { name: "dup", id: 7, xmpMetadata: "" };
        (app as MutableApp).activeDocument = { layers: [decoy, intended] };
        await renameLayer(["dup"], "dup [mesh]", 99);
        expect(intended.name).toBe("dup [mesh]");
        expect(decoy.name).toBe("dup");
    });

    // Keep last: this mocks executeAsModal to reject; vitest's
    // restoreAllMocks does not fully reset the module-level vi.fn, so a
    // later test would inherit the rejection.
    it("reports the error when the modal rejects", async () => {
        (app as MutableApp).activeDocument = { layers: [{ name: "torso" }] };
        vi.spyOn(core, "executeAsModal").mockRejectedValue(new Error("modal denied"));
        expect(await renameLayer(["torso"], "x")).toEqual({ ok: false, reason: "modal denied" });
    });
});
