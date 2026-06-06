// the photoshop tag system: XMP mirror for the bracket-tag canonical.
// Bracket tags in the layer name remain the source of truth; this
// module additionally stamps the same `TagBag` into document-level
// XMP under the `proscenio` namespace (`urn:proscenio:tags:v1`),
// keyed by sanitised layer path. Read paths still
// trust the name (name wins on conflict); the mirror is
// secondary, defensive, and best-effort.
//
// Every operation is wrapped so failures never block the rename
// pipeline. If the host build does not expose `uxp.xmp` or the PSD
// metadata reader rejects the call, the mirror silently degrades to
// a no-op and a debug log line.

import { xmp as uxpXmp } from "uxp";
import type { PsLayer } from "photoshop";

import type { TagBag } from "../lib/tag-parser";
import { log } from "../util/log";

export const PROSCENIO_XMP_NAMESPACE_URI = "urn:proscenio:tags:v1";
export const PROSCENIO_XMP_PREFIX = "proscenio";
const XMP_PROPERTY_PREFIX = "tag_";

// XMP local names must follow XML NCName rules: letters, digits,
// underscore, hyphen, period; cannot contain `/` or whitespace. PSD
// layer names happily include both, so we sanitise the path before
// passing it to `setProperty`. Two distinct paths can collide here
// (rare in practice); the bracket-tag canonical store is authoritative
// regardless.
function xmpPropertyName(layerPath: readonly string[]): string {
    const joined = layerPath.join("__");
    const safe = joined.replaceAll(/[^A-Za-z0-9_\-.]/g, "_");
    return XMP_PROPERTY_PREFIX + safe;
}

export function isXmpAvailable(): boolean {
    return uxpXmp !== undefined && typeof uxpXmp.XMPMeta === "function";
}

export class XmpUnavailableError extends Error {
    constructor() {
        super(
            "uxp.xmp is not available in this Photoshop build. the photoshop tag system tag mirroring "
                + "requires PS 25 / CC 2024 or later; update Photoshop to enable the XMP layer.",
        );
        this.name = "XmpUnavailableError";
    }
}

/** Best-effort: stamp the bracket-tag bag into the layer's XMP record
 *  under the proscenio namespace. Returns `true` when the write
 *  succeeded; `false` (with a log line) on any failure or when the
 *  XMP API is unavailable. Never throws. */
export function writeLayerTagsToXmp(
    layer: PsLayer,
    layerPath: readonly string[],
    tags: TagBag,
): boolean {
    if (uxpXmp === undefined) {
        log.debug("xmp", "uxp.xmp unavailable; skipping mirror write");
        return false;
    }
    try {
        const raw = layer.xmpMetadata ?? layer.metadata?.xmp ?? "";
        const meta = new uxpXmp.XMPMeta(raw);
        uxpXmp.XMPMeta.registerNamespace?.(PROSCENIO_XMP_NAMESPACE_URI, PROSCENIO_XMP_PREFIX);
        const key = xmpPropertyName(layerPath);
        const value = JSON.stringify(serializableTagBag(tags));
        meta.setProperty(PROSCENIO_XMP_NAMESPACE_URI, key, value);
        layer.xmpMetadata = meta.serialize();
        return true;
    } catch (err) {
        log.debug("xmp", "writeLayerTagsToXmp failed (non-fatal)", err);
        return false;
    }
}

/** Reads the mirrored `TagBag` for a layer path, if present. Returns
 *  `null` when the XMP API is unavailable, the property is absent,
 *  or the stored JSON is unparsable. Never throws. */
export function readLayerTagsFromXmp(
    layer: PsLayer,
    layerPath: readonly string[],
): TagBag | null {
    if (uxpXmp === undefined) return null;
    try {
        const raw = layer.xmpMetadata ?? layer.metadata?.xmp ?? "";
        if (raw === "") return null;
        const meta = new uxpXmp.XMPMeta(raw);
        const key = xmpPropertyName(layerPath);
        const prop = meta.getProperty(PROSCENIO_XMP_NAMESPACE_URI, key);
        if (prop?.value === undefined) return null;
        const parsed: unknown = JSON.parse(prop.value);
        // XMP is external, user-editable metadata. Validate the shape
        // before letting it into the domain; a malformed record degrades
        // to null (the bracket-tag canonical store is authoritative).
        if (!isTagBag(parsed)) return null;
        return parsed;
    } catch (err) {
        log.debug("xmp", "readLayerTagsFromXmp failed (non-fatal)", err);
        return null;
    }
}

function isTagBag(value: unknown): value is TagBag {
    if (typeof value !== "object" || value === null) return false;
    const v = value as Record<string, unknown>;
    const optBool = (x: unknown): boolean => x === undefined || x === true;
    const optStr = (x: unknown): boolean => x === undefined || typeof x === "string";
    const optNum = (x: unknown): boolean => x === undefined || typeof x === "number";
    const optOrigin = (x: unknown): boolean =>
        x === undefined
        || (Array.isArray(x) && x.length === 2 && x.every((n) => typeof n === "number"));
    return (
        optBool(v["ignore"])
        && optBool(v["merge"])
        && optBool(v["originMarker"])
        && optStr(v["folder"])
        && optStr(v["kind"])
        && optStr(v["path"])
        && optStr(v["blend"])
        && optStr(v["namePattern"])
        && optNum(v["scale"])
        && optOrigin(v["origin"])
    );
}

function serializableTagBag(tags: TagBag): Record<string, unknown> {
    // Drop `undefined` fields explicitly so the JSON stays compact.
    // TagBag uses an index signature so bracket access satisfies the
    // `noPropertyAccessFromIndexSignature` rule.
    const out: Record<string, unknown> = {};
    if (tags.ignore === true) out["ignore"] = true;
    if (tags.merge === true) out["merge"] = true;
    if (tags.kind !== undefined) out["kind"] = tags.kind;
    if (tags.folder !== undefined) out["folder"] = tags.folder;
    if (tags.path !== undefined) out["path"] = tags.path;
    if (tags.blend !== undefined) out["blend"] = tags.blend;
    if (tags.scale !== undefined) out["scale"] = tags.scale;
    if (tags.origin !== undefined) out["origin"] = tags.origin;
    if (tags.originMarker === true) out["originMarker"] = true;
    if (tags.namePattern !== undefined) out["namePattern"] = tags.namePattern;
    return out;
}
