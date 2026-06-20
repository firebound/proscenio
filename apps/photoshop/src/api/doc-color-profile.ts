// Document color-profile guard for the Validate panel.
//
// Godot - and game engines generally - ignore an image's embedded ICC profile
// and read the PNG bytes as sRGB. A PSD authored in a wider space (Adobe RGB
// (1998), Display P3, ProPhoto) therefore has its out-of-gamut colors clamped
// when exported to the sRGB the engine expects, so what the artist painted is
// not what the game shows. This module classifies the active document's profile
// so the panel can warn before that surprise.
//
// The classification is a pure string check (unit-tested). The read is a thin
// synchronous DOM accessor: UXP surfaces `Document.colorProfileName` directly,
// returning the literal "None" when the document is not color-managed - which
// we treat as "unknown" (the working space governs export, so we cannot call it
// wrong) rather than as a warning.

import type { PsDocument } from "photoshop";

export type ColorProfileStatus =
    | { kind: "srgb"; profile: string }
    | { kind: "non-srgb"; profile: string }
    | { kind: "unknown" };

/** Classify a raw profile name. Anything we cannot positively read as a named,
 *  non-sRGB profile resolves to "unknown" so the panel never warns on a false
 *  positive: an untagged document (the "None" marker), an empty value, or an
 *  older UXP build that omits the property. */
export function classifyColorProfile(profileName: string | null | undefined): ColorProfileStatus {
    if (typeof profileName !== "string") return { kind: "unknown" };
    const name = profileName.trim();
    if (name === "" || name.toLowerCase() === "none") return { kind: "unknown" };
    if (/srgb/i.test(name)) return { kind: "srgb", profile: name };
    return { kind: "non-srgb", profile: name };
}

/** Read + classify the active document's color profile. Synchronous; tolerant
 *  of builds that omit `colorProfileName`. */
export function readDocColorProfile(doc: PsDocument): ColorProfileStatus {
    return classifyColorProfile(doc.colorProfileName);
}
