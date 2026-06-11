// Pure model behind the Tags "advanced fields" expander
// (`panels/sections/tags/Details`). Holds the string-keyed draft shape
// the inputs bind to, plus the baseline diff that turns an edited form
// into a minimal `Partial<TagBag>` for one rename call. Value checks
// reuse the bracket-tag parser's validators so the form accepts exactly
// what the parser would accept. No React, no UXP - unit-testable.

import type { TagBag } from "./tag-parser";
import { isValidNamePattern, isValidPathValue, parseScaleValue } from "./tag-parser";

export interface DetailForm {
    folder: string;
    path: string;
    scale: string;
    originX: string;
    originY: string;
    originMarker: boolean;
    namePattern: string;
}

export function formFromTags(tags: TagBag): DetailForm {
    return {
        folder: tags.folder ?? "",
        path: tags.path ?? "",
        scale: tags.scale === undefined ? "" : String(tags.scale),
        originX: tags.origin === undefined ? "" : String(tags.origin[0]),
        originY: tags.origin === undefined ? "" : String(tags.origin[1]),
        originMarker: tags.originMarker === true,
        namePattern: tags.namePattern ?? "",
    };
}

export function formsEqual(a: DetailForm, b: DetailForm): boolean {
    return (
        a.folder === b.folder
        && a.path === b.path
        && a.scale === b.scale
        && a.originX === b.originX
        && a.originY === b.originY
        && a.originMarker === b.originMarker
        && a.namePattern === b.namePattern
    );
}

// The minimal edit one Apply fires: keys to write (`set`) and keys to
// delete (`clear`). Two channels rather than one `Partial<TagBag>`
// because `exactOptionalPropertyTypes` forbids a present `undefined`
// member, so a cleared field cannot ride the bag as `{ key: undefined }`
// - it would be dropped, which is the form-clear bug this shape fixes.
export interface TagChanges {
    set: Partial<TagBag>;
    clear: (keyof TagBag)[];
}

// Sentinel returned by `diff*` helpers when the form value matches the
// baseline (or is invalid and should be left alone). Distinct symbol so
// the diff type cannot collapse with `string`-typed fields
// (TagBag.folder, TagBag.path, etc). `undefined` means "clear the tag";
// a concrete value means "set it".
const SKIP = Symbol("skip");
type Diff<T> = T | undefined | typeof SKIP;

function diffFolder(form: DetailForm, baseline: DetailForm): Diff<TagBag["folder"]> {
    const value = form.folder.trim();
    if (value === baseline.folder.trim()) return SKIP;
    return value.length === 0 ? undefined : value;
}

function diffPath(form: DetailForm, baseline: DetailForm): Diff<TagBag["path"]> {
    const value = form.path.trim();
    if (value === baseline.path.trim()) return SKIP;
    if (value.length === 0) return undefined;
    return isValidPathValue(value) ? value : SKIP;
}

function diffScale(form: DetailForm, baseline: DetailForm): Diff<TagBag["scale"]> {
    const value = form.scale.trim();
    if (value === baseline.scale.trim()) return SKIP;
    if (value.length === 0) return undefined;
    return parseScaleValue(value) ?? SKIP;
}

function diffOrigin(form: DetailForm, baseline: DetailForm): Diff<TagBag["origin"]> {
    const ox = form.originX.trim();
    const oy = form.originY.trim();
    if (ox === baseline.originX.trim() && oy === baseline.originY.trim()) return SKIP;
    if (ox.length === 0 && oy.length === 0) return undefined;
    const x = Number.parseFloat(ox);
    const y = Number.parseFloat(oy);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return SKIP;
    return [x, y];
}

function diffNamePattern(form: DetailForm, baseline: DetailForm): Diff<TagBag["namePattern"]> {
    const value = form.namePattern.trim();
    if (value === baseline.namePattern.trim()) return SKIP;
    if (value.length === 0) return undefined;
    return isValidNamePattern(value) ? value : SKIP;
}

function applyDiff<K extends keyof TagBag>(
    changes: TagChanges,
    key: K,
    diff: Diff<TagBag[K]>,
): void {
    if (diff === SKIP) return;
    if (diff === undefined) {
        changes.clear.push(key);
        return;
    }
    changes.set[key] = diff;
}

export function computeChanges(form: DetailForm, baseline: DetailForm): TagChanges {
    const changes: TagChanges = { set: {}, clear: [] };
    applyDiff(changes, "folder", diffFolder(form, baseline));
    applyDiff(changes, "path", diffPath(form, baseline));
    applyDiff(changes, "scale", diffScale(form, baseline));
    applyDiff(changes, "origin", diffOrigin(form, baseline));
    if (form.originMarker !== baseline.originMarker) {
        if (form.originMarker) {
            changes.set.originMarker = true;
        } else {
            changes.clear.push("originMarker");
        }
    }
    applyDiff(changes, "namePattern", diffNamePattern(form, baseline));
    return changes;
}
