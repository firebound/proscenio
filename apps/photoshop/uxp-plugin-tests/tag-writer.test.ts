// Round-trip tests for the bracket-tag writer. Every produced name
// must parse back into the same TagBag.

import { describe, expect, it } from "vitest";

import { parseLayerName, type TagBag } from "../src/domain/tag-parser";
import {
    setBlendTag,
    setKindTag,
    toggleTag,
    writeLayerName,
} from "../src/domain/tag-writer";

function roundtrip(displayName: string, tags: TagBag): TagBag {
    const written = writeLayerName(displayName, tags);
    return parseLayerName(written).tags;
}

describe("writeLayerName", () => {
    it("emits an empty tag list when bag is empty", () => {
        expect(writeLayerName("torso", {})).toBe("torso");
    });

    it("appends [ignore]", () => {
        expect(writeLayerName("helper", { ignore: true })).toBe("helper [ignore]");
    });

    it("orders ignore before merge before kind", () => {
        const out = writeLayerName("body", { ignore: true, merge: true, kind: "mesh" });
        expect(out).toBe("body [ignore] [merge] [mesh]");
    });

    it("emits [spritesheet] for sprite_frame kind", () => {
        expect(writeLayerName("blink", { kind: "sprite_frame" })).toBe("blink [spritesheet]");
    });

    it("formats folder + path + blend + scale", () => {
        const out = writeLayerName("eye", {
            folder: "eyes",
            path: "iris",
            blend: "multiply",
            scale: 0.5,
        });
        expect(out).toBe("eye [folder:eyes] [path:iris] [blend:multiply] [scale:0.5]");
    });

    it("formats explicit origin and never adds the bare marker too", () => {
        const out = writeLayerName("arm", { origin: [10, 20], originMarker: true });
        expect(out).toBe("arm [origin:10,20]");
    });

    it("emits the bare origin marker when no explicit coords", () => {
        expect(writeLayerName("pivot", { originMarker: true })).toBe("pivot [origin]");
    });

    it("works when displayName is empty", () => {
        expect(writeLayerName("", { ignore: true })).toBe("[ignore]");
    });
});

describe("writeLayerName round-trips through parseLayerName", () => {
    const cases: { name: string; tags: TagBag }[] = [
        { name: "ignored", tags: { ignore: true } },
        { name: "body", tags: { merge: true, kind: "mesh" } },
        { name: "blink", tags: { kind: "sprite_frame" } },
        { name: "eye", tags: { folder: "eyes", blend: "multiply", scale: 2 } },
        { name: "pivot", tags: { origin: [10, 20] } },
        { name: "head", tags: { originMarker: true } },
        { name: "tile", tags: { path: "tile-01" } },
        { name: "group", tags: { namePattern: "pre*suf" } },
    ];
    it.each(cases)("$name", ({ name, tags }) => {
        expect(roundtrip(name, tags)).toEqual(tags);
    });
});

describe("toggleTag", () => {
    it("adds the flag when enabled", () => {
        const next = toggleTag("torso", {}, "ignore", true);
        expect(parseLayerName(next).tags.ignore).toBe(true);
    });

    it("removes the flag when disabled", () => {
        const next = toggleTag("torso", { ignore: true }, "ignore", false);
        expect(parseLayerName(next).tags.ignore).toBeUndefined();
    });
});

describe("setKindTag", () => {
    it("sets the kind", () => {
        const next = setKindTag("body", {}, "mesh");
        expect(parseLayerName(next).tags.kind).toBe("mesh");
    });

    it("clears the kind", () => {
        const next = setKindTag("body", { kind: "mesh" }, undefined);
        expect(parseLayerName(next).tags.kind).toBeUndefined();
    });
});

describe("setBlendTag", () => {
    it("rewrites blend cleanly", () => {
        const next = setBlendTag("a", { blend: "multiply" }, "additive");
        expect(parseLayerName(next).tags.blend).toBe("additive");
    });

    it("clears blend when undefined", () => {
        const next = setBlendTag("a", { blend: "multiply" }, undefined);
        expect(parseLayerName(next).tags.blend).toBeUndefined();
    });
});
