// Shared key derivation for the Tags-tab collapse/expand state Set.
// ProscenioTagsPanel owns the Set; TagsSection looks up against it.
// Both sides must agree on the join character or toggles never match.
//
// Photoshop allows almost any character in a layer name, including
// forward slash. Joining displayPath segments with "/" therefore
// risks colliding ["a/b"] with ["a", "b"]. The U+0001 (Start of
// Heading) control character is not addressable from the Layers
// panel UI and never appears in a real layer name, so it is safe as
// a structural delimiter that survives any artist input.

export const COLLAPSE_KEY_DELIMITER = "";

export function collapseKey(displayPath: readonly string[]): string {
    return displayPath.join(COLLAPSE_KEY_DELIMITER);
}
