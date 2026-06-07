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

    it("reports the error when the modal rejects", async () => {
        (app as MutableApp).activeDocument = { layers: [{ name: "torso" }] };
        vi.spyOn(core, "executeAsModal").mockRejectedValue(new Error("modal denied"));
        expect(await renameLayer(["torso"], "x")).toEqual({ ok: false, reason: "modal denied" });
    });
});
