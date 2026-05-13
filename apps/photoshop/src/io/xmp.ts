// SPEC 011 D2 + Wave 11.6: XMP mirror for the bracket-tag canonical.
// Bracket tags in the layer name remain the source of truth; this
// module additionally stamps the same `TagBag` into document-level
// XMP under `proscenio:v1:layers/<layer-path>`. Read paths still
// trust the name (D9 says name wins on conflict); the mirror is
// secondary, defensive, and best-effort.
//
// Every operation is wrapped so failures never block the rename
// pipeline. If the host build does not expose `uxp.xmp` or the PSD
// metadata reader rejects the call, the mirror silently degrades to
// a no-op and a debug log line.

import * as uxpModule from "uxp";
import type { PsLayer } from "photoshop";

import type { TagBag } from "../domain/tag-parser";
import { log } from "../util/log";

export const PROSCENIO_XMP_NAMESPACE_URI = "https://proscenio.dev/spec-011/v1";
export const PROSCENIO_XMP_PREFIX = "proscenio";
const XMP_PROPERTY_PREFIX = "tags/";

interface XMPMetaCtor {
    new (raw?: string): XMPMetaInstance;
    registerNamespace?(uri: string, prefix: string): void;
}

interface XMPMetaInstance {
    serialize(): string;
    setProperty(ns: string, key: string, value: string): void;
    getProperty(ns: string, key: string): { value?: string } | undefined;
    deleteProperty(ns: string, key: string): void;
    doesPropertyExist?(ns: string, key: string): boolean;
}

interface XmpModuleShape {
    XMPMeta?: XMPMetaCtor;
}

interface DocumentMetadataCarrier {
    xmpMetadata?: string;
    metadata?: { xmp?: string };
}

function xmpModule(): XmpModuleShape | undefined {
    return (uxpModule as unknown as { xmp?: XmpModuleShape }).xmp;
}

export function isXmpAvailable(): boolean {
    const candidate = xmpModule();
    return candidate !== undefined && typeof candidate.XMPMeta === "function";
}

export class XmpUnavailableError extends Error {
    constructor() {
        super(
            "uxp.xmp is not available in this Photoshop build. SPEC 011 tag mirroring "
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
    const mod = xmpModule();
    if (mod?.XMPMeta === undefined) {
        log.debug("xmp", "uxp.xmp unavailable; skipping mirror write");
        return false;
    }
    try {
        const carrier = layer as unknown as DocumentMetadataCarrier;
        const raw = carrier.xmpMetadata ?? carrier.metadata?.xmp ?? "";
        const meta = new mod.XMPMeta(raw);
        mod.XMPMeta.registerNamespace?.(PROSCENIO_XMP_NAMESPACE_URI, PROSCENIO_XMP_PREFIX);
        const key = XMP_PROPERTY_PREFIX + layerPath.join("/");
        const value = JSON.stringify(serializableTagBag(tags));
        meta.setProperty(PROSCENIO_XMP_NAMESPACE_URI, key, value);
        carrier.xmpMetadata = meta.serialize();
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
    const mod = xmpModule();
    if (mod?.XMPMeta === undefined) return null;
    try {
        const carrier = layer as unknown as DocumentMetadataCarrier;
        const raw = carrier.xmpMetadata ?? carrier.metadata?.xmp ?? "";
        if (raw === "") return null;
        const meta = new mod.XMPMeta(raw);
        const key = XMP_PROPERTY_PREFIX + layerPath.join("/");
        const prop = meta.getProperty(PROSCENIO_XMP_NAMESPACE_URI, key);
        if (prop?.value === undefined) return null;
        const parsed: unknown = JSON.parse(prop.value);
        if (typeof parsed !== "object" || parsed === null) return null;
        return parsed as TagBag;
    } catch (err) {
        log.debug("xmp", "readLayerTagsFromXmp failed (non-fatal)", err);
        return null;
    }
}

function serializableTagBag(tags: TagBag): Record<string, unknown> {
    // Drop `undefined` fields explicitly so the JSON stays compact.
    const out: Record<string, unknown> = {};
    if (tags.ignore === true) out.ignore = true;
    if (tags.merge === true) out.merge = true;
    if (tags.kind !== undefined) out.kind = tags.kind;
    if (tags.folder !== undefined) out.folder = tags.folder;
    if (tags.path !== undefined) out.path = tags.path;
    if (tags.blend !== undefined) out.blend = tags.blend;
    if (tags.scale !== undefined) out.scale = tags.scale;
    if (tags.origin !== undefined) out.origin = tags.origin;
    if (tags.originMarker === true) out.originMarker = true;
    if (tags.namePattern !== undefined) out.namePattern = tags.namePattern;
    return out;
}
