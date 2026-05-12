// Unit tests for the bracket-tag lexer (SPEC 011 Wave 11.1).

import { describe, expect, it } from "vitest";

import { parseLayerName } from "../src/domain/tag-parser";

describe("parseLayerName - basics", () => {
    it("returns the raw name when no tags are present", () => {
        expect(parseLayerName("torso")).toEqual({ displayName: "torso", tags: {} });
    });

    it("strips a leading tag and collapses whitespace", () => {
        const r = parseLayerName("[ignore] head");
        expect(r.displayName).toBe("head");
        expect(r.tags.ignore).toBe(true);
    });

    it("strips a trailing tag", () => {
        const r = parseLayerName("head [ignore]");
        expect(r.displayName).toBe("head");
        expect(r.tags.ignore).toBe(true);
    });

    it("strips multiple tags from any position", () => {
        const r = parseLayerName("[scale:2] arm [folder:body] [path:custom]");
        expect(r.displayName).toBe("arm");
        expect(r.tags.scale).toBe(2);
        expect(r.tags.folder).toBe("body");
        expect(r.tags.path).toBe("custom");
    });

    it("keeps unknown brackets in the display name", () => {
        const r = parseLayerName("arm [OLD] [ignore]");
        expect(r.displayName).toBe("arm [OLD]");
        expect(r.tags.ignore).toBe(true);
    });

    it("is case-insensitive on the tag keyword", () => {
        const r = parseLayerName("head [IGNORE]");
        expect(r.tags.ignore).toBe(true);
        expect(r.displayName).toBe("head");
    });
});

describe("parseLayerName - kind overrides", () => {
    it("[polygon] sets kind polygon", () => {
        expect(parseLayerName("x [polygon]").tags.kind).toBe("polygon");
    });

    it("[sprite] is an alias for polygon", () => {
        expect(parseLayerName("x [sprite]").tags.kind).toBe("polygon");
    });

    it("[mesh] sets kind mesh", () => {
        expect(parseLayerName("x [mesh]").tags.kind).toBe("mesh");
    });

    it("[spritesheet] translates to sprite_frame kind", () => {
        expect(parseLayerName("x [spritesheet]").tags.kind).toBe("sprite_frame");
    });
});

describe("parseLayerName - origin", () => {
    it("[origin] alone marks the layer as origin marker", () => {
        const r = parseLayerName("pivot [origin]");
        expect(r.tags.originMarker).toBe(true);
        expect(r.tags.origin).toBeUndefined();
    });

    it("[origin:x,y] sets explicit origin coordinates", () => {
        const r = parseLayerName("arm [origin:50,75]");
        expect(r.tags.origin).toEqual([50, 75]);
        expect(r.tags.originMarker).toBeUndefined();
    });

    it("[origin:malformed] is rejected and stays in display name", () => {
        const r = parseLayerName("arm [origin:abc]");
        expect(r.tags.origin).toBeUndefined();
        expect(r.tags.originMarker).toBeUndefined();
        expect(r.displayName).toBe("arm [origin:abc]");
    });
});

describe("parseLayerName - scale / blend / path / folder", () => {
    it("[scale:1.5] parses a float", () => {
        expect(parseLayerName("x [scale:1.5]").tags.scale).toBe(1.5);
    });

    it("[scale:0] is rejected (non-positive)", () => {
        const r = parseLayerName("x [scale:0]");
        expect(r.tags.scale).toBeUndefined();
        expect(r.displayName).toBe("x [scale:0]");
    });

    it("[blend:multiply] parses a known mode", () => {
        expect(parseLayerName("x [blend:multiply]").tags.blend).toBe("multiply");
    });

    it("[blend:nonsense] is rejected", () => {
        const r = parseLayerName("x [blend:nonsense]");
        expect(r.tags.blend).toBeUndefined();
        expect(r.displayName).toBe("x [blend:nonsense]");
    });

    it("[path:name] parses verbatim", () => {
        expect(parseLayerName("x [path:custom_file]").tags.path).toBe("custom_file");
    });

    it("[folder:name] parses verbatim", () => {
        expect(parseLayerName("x [folder:body]").tags.folder).toBe("body");
    });

    it("[folder:] empty value is rejected", () => {
        const r = parseLayerName("x [folder:]");
        expect(r.tags.folder).toBeUndefined();
    });
});

describe("parseLayerName - name pattern macro", () => {
    it("[name:pre*suf] keeps the pattern verbatim", () => {
        expect(parseLayerName("body [name:hero_*]").tags.namePattern).toBe("hero_*");
    });

    it("[name:no-asterisk] is rejected", () => {
        const r = parseLayerName("body [name:hero_]");
        expect(r.tags.namePattern).toBeUndefined();
        expect(r.displayName).toBe("body [name:hero_]");
    });
});
