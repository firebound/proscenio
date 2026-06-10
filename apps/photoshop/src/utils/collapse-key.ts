// Shared key derivation for the Tags-tab collapse/expand state Set.
// The panel that owns the Set and the section that looks up against it
// must agree on this join character or toggles never match.
//
// Photoshop allows almost any character in a layer name, including
// forward slash, so joining displayPath segments with "/" would collide
// ["a/b"] with ["a", "b"]. U+0001 (Start of Heading) is not addressable
// from the Layers panel UI and never appears in a real layer name, so
// it is a safe structural delimiter.

export const COLLAPSE_KEY_DELIMITER = "";

export function collapseKey(displayPath: readonly string[]): string {
    return displayPath.join(COLLAPSE_KEY_DELIMITER);
}
