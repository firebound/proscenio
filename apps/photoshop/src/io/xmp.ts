// SPEC 011 Wave 11.6: defensive guard around `uxp.xmp`. The plugin's
// `host.minVersion` already enforces PS 25 / CC 2024+, which is the
// version that ships `uxp.xmp`. This module exists so the Tags tab
// (Wave 11.3) can surface a clear error when the API is unexpectedly
// missing rather than crashing in the middle of a tag write.
//
// The full read / write surface (proscenio:v1 XMP namespace mirror for
// bracket tags) is wired up in Wave 11.3; this file currently only
// exposes the availability probe + the namespace constants.

import * as uxpModule from "uxp";

export const PROSCENIO_XMP_NAMESPACE_URI = "https://proscenio.dev/spec-011/v1";
export const PROSCENIO_XMP_PREFIX = "proscenio";

interface XmpModuleShape {
    XMPMeta?: unknown;
}

export function isXmpAvailable(): boolean {
    const candidate = (uxpModule as unknown as { xmp?: XmpModuleShape }).xmp;
    return candidate !== undefined && candidate.XMPMeta !== undefined;
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
