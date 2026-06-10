// Bracket-tag parser. Lexes `[tag]` and `[tag:value]` tokens out of a
// PSD layer or group name, returning the stripped display name plus a
// structured tag bag.
//
// Conventions (the photoshop tag system):
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
// happens here at parse time. `[sprite]` / `[spritesheet]` become
// `kind: "sprite"`; the manifest never sees the tag name.

import type { BlendMode } from "./manifest";

export interface TagBag {
    ignore?: true;
    merge?: true;
    folder?: string;
    /** Explicit kind override. `[mesh]` / `[poly]` / `[polygon]` -> mesh; `[sprite]` / `[spritesheet]` -> sprite. */
    kind?: "mesh" | "sprite";
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

// Shared tag-value validators. Exported so the Tags advanced-fields
// form (`lib/tag-form`) validates typed input against the exact rules
// the parser enforces, with no second copy of the checks to drift out
// of sync. Both the parser's `consume*` helpers and the form's diff
// helpers call these.

/** `[scale:N]` value -> positive finite number, or `null` when invalid.
 *  `Number.parseFloat` would accept "1abc" as 1, so a strict numeric
 *  pattern (digits + optional fractional part) gates the cast. */
export function parseScaleValue(value: string): number | null {
    if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(value)) return null;
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return null;
    return n;
}

/** `[path:NAME]` filename-stem rule: non-empty, no path separators, not
 *  a parent-dir segment. Rejecting `/`, `\`, `.` and `..` stops a tag
 *  from escaping the output folder via `[path:../foo]` or carving
 *  unintended subdirectories (`[folder:name]` owns subfolders). */
export function isValidPathValue(value: string): boolean {
    return (
        value.length > 0
        && !value.includes("/")
        && !value.includes("\\")
        && value !== "."
        && value !== ".."
    );
}

/** `[name:pre*suf]` group macro: non-empty and contains the `*`
 *  wildcard that substitutes the original child name. */
export function isValidNamePattern(value: string): boolean {
    return value.length > 0 && value.includes("*");
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
        case "mesh":
        case "poly":
        case "polygon":
            tags.kind = "mesh";
            return true;
        case "sprite":
        case "spritesheet":
            tags.kind = "sprite";
            return true;
        case "origin":
            return consumeOrigin(value, tags);
        case "scale":
            return consumeScale(value, tags);
        case "blend":
            return consumeBlend(value, tags);
        case "path":
            if (!isValidPathValue(value)) return false;
            tags.path = value;
            return true;
        case "name":
            if (!isValidNamePattern(value)) return false;
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
    const x = match?.[1];
    const y = match?.[2];
    if (x === undefined || y === undefined) return false;
    tags.origin = [Number.parseFloat(x), Number.parseFloat(y)];
    return true;
}

function consumeScale(value: string, tags: TagBag): boolean {
    const n = parseScaleValue(value);
    if (n === null) return false;
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
