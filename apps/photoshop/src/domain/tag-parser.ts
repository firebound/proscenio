// Bracket-tag parser. Lexes `[tag]` and `[tag:value]` tokens out of a
// PSD layer or group name, returning the stripped display name plus a
// structured tag bag.
//
// Conventions (SPEC 011 D1, D5):
//
// - Tags may appear anywhere in the name. `head [ignore]`, `[ignore]
//   head`, and `arm [folder:body] [scale:0.5]` are all valid.
// - Unknown brackets (`[OLD]`, `[Final]`) pass through unchanged as
//   part of the display name. The parser only consumes tokens whose
//   left-hand side matches the locked vocabulary.
// - Whitespace adjacent to a stripped tag collapses to a single space;
//   leading / trailing whitespace is trimmed.
// - Tag matching is case-insensitive on the keyword; values are kept
//   verbatim.
//
// The translation from artist-friendly tag name to manifest field
// happens here at parse time. `[spritesheet]` becomes
// `kind: "sprite_frame"`; the manifest never sees the tag name.

import type { BlendMode } from "./manifest";

export type PolygonKind = "polygon" | "mesh";

export interface TagBag {
    ignore?: true;
    merge?: true;
    folder?: string;
    /** Explicit kind override. `[polygon]` / `[sprite]` -> polygon; `[mesh]` -> mesh; `[spritesheet]` -> sprite_frame. */
    kind?: PolygonKind | "sprite_frame";
    /** Mark this layer as the group's origin marker (no PNG emitted). */
    originMarker?: true;
    /** Explicit pivot in PSD pixels (set by `[origin:x,y]`). */
    origin?: [number, number];
    scale?: number;
    blend?: BlendMode;
    /** Override for the on-disk filename (without extension). */
    path?: string;
    /** Group-only: child-name pattern macro (`[name:pre*suf]`). `*` substitutes the original child name. */
    namePattern?: string;
}

export interface ParsedName {
    displayName: string;
    tags: TagBag;
}

// `[keyword]` or `[keyword:value]`. Keyword must start with a letter
// (so plain `[123]` does not collide with the parser). Value accepts
// any character except a closing bracket; whitespace is trimmed in
// `consumeToken`. The pattern is intentionally permissive on the
// value so `[name:pre*suf]` and `[path:my-file.v2]` work.
const TAG_PATTERN = /\[([A-Za-z][^\]]*?)\]/g;

export function parseLayerName(raw: string): ParsedName {
    const tags: TagBag = {};
    const stripped = raw.replaceAll(TAG_PATTERN, (match, body: string) => {
        return consumeToken(body, tags) ? "" : match;
    });
    return { displayName: collapseWhitespace(stripped), tags };
}

function consumeToken(body: string, tags: TagBag): boolean {
    const colon = body.indexOf(":");
    const key = (colon === -1 ? body : body.slice(0, colon)).toLowerCase();
    const value = colon === -1 ? "" : body.slice(colon + 1).trim();
    switch (key) {
        case "ignore":
            tags.ignore = true;
            return true;
        case "merge":
            tags.merge = true;
            return true;
        case "folder":
            if (value.length === 0) return false;
            tags.folder = value;
            return true;
        case "polygon":
        case "sprite":
            tags.kind = "polygon";
            return true;
        case "mesh":
            tags.kind = "mesh";
            return true;
        case "spritesheet":
            tags.kind = "sprite_frame";
            return true;
        case "origin":
            return consumeOrigin(value, tags);
        case "scale":
            return consumeScale(value, tags);
        case "blend":
            return consumeBlend(value, tags);
        case "path":
            if (value.length === 0) return false;
            tags.path = value;
            return true;
        case "name":
            // `[name:pre*suf]` group pattern macro. Reject when missing the `*`.
            if (value.length === 0 || !value.includes("*")) return false;
            tags.namePattern = value;
            return true;
        default:
            return false;
    }
}

function consumeOrigin(value: string, tags: TagBag): boolean {
    if (value.length === 0) {
        tags.originMarker = true;
        return true;
    }
    const match = /^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/.exec(value);
    if (match === null) return false;
    tags.origin = [Number.parseFloat(match[1]), Number.parseFloat(match[2])];
    return true;
}

function consumeScale(value: string, tags: TagBag): boolean {
    if (value.length === 0) return false;
    const n = Number.parseFloat(value);
    if (!Number.isFinite(n) || n <= 0) return false;
    tags.scale = n;
    return true;
}

function consumeBlend(value: string, tags: TagBag): boolean {
    const lc = value.toLowerCase();
    if (lc !== "normal" && lc !== "multiply" && lc !== "screen" && lc !== "additive") {
        return false;
    }
    tags.blend = lc;
    return true;
}

function collapseWhitespace(s: string): string {
    return s.replaceAll(/\s+/g, " ").trim();
}
