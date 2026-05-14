// Advanced tag-fields panel (the `+` expander on each row).
//
// Inputs are controlled by a LOCAL draft state. Typing / blurring does
// not commit - the Apply button computes the delta vs the baseline
// (current node.tags) and fires one rename call. External renames
// (toggle X clicked, kind dropdown picked, etc.) reset the form so it
// keeps showing the truth on disk.

import React from "react";

import type { TagBag } from "../../../domain/tag-parser";
import type { TagTreeNode } from "../../../domain/tag-tree";
import { readSelectionCenter } from "../../../io/ps-selection-bounds";
import { log } from "../../../util/log";

interface DetailForm {
    folder: string;
    path: string;
    scale: string;
    originX: string;
    originY: string;
    originMarker: boolean;
    namePattern: string;
}

function formFromTags(tags: TagBag): DetailForm {
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

function formsEqual(a: DetailForm, b: DetailForm): boolean {
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

function diffFolder(form: DetailForm, baseline: DetailForm): TagBag["folder"] | undefined | "skip" {
    const value = form.folder.trim();
    if (value === baseline.folder.trim()) return "skip";
    return value.length === 0 ? undefined : value;
}

function diffPath(form: DetailForm, baseline: DetailForm): TagBag["path"] | undefined | "skip" {
    const value = form.path.trim();
    if (value === baseline.path.trim()) return "skip";
    if (value.length === 0) return undefined;
    if (value.includes("/") || value.includes("\\") || value === "." || value === "..") return "skip";
    return value;
}

function diffScale(form: DetailForm, baseline: DetailForm): TagBag["scale"] | undefined | "skip" {
    const value = form.scale.trim();
    if (value === baseline.scale.trim()) return "skip";
    if (value.length === 0) return undefined;
    if (!/^(?:\d+\.?\d*|\.\d+)$/.test(value)) return "skip";
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return "skip";
    return n;
}

function diffOrigin(form: DetailForm, baseline: DetailForm): TagBag["origin"] | undefined | "skip" {
    const ox = form.originX.trim();
    const oy = form.originY.trim();
    if (ox === baseline.originX.trim() && oy === baseline.originY.trim()) return "skip";
    if (ox.length === 0 && oy.length === 0) return undefined;
    const x = Number.parseFloat(ox);
    const y = Number.parseFloat(oy);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return "skip";
    return [x, y];
}

function diffNamePattern(form: DetailForm, baseline: DetailForm): TagBag["namePattern"] | undefined | "skip" {
    const value = form.namePattern.trim();
    if (value === baseline.namePattern.trim()) return "skip";
    if (value.length === 0) return undefined;
    if (!value.includes("*")) return "skip";
    return value;
}

function applyDiff<K extends keyof TagBag>(
    changes: Partial<TagBag>,
    key: K,
    diff: TagBag[K] | undefined | "skip",
): void {
    if (diff === "skip") return;
    changes[key] = diff;
}

function computeChanges(form: DetailForm, baseline: DetailForm): Partial<TagBag> {
    const changes: Partial<TagBag> = {};
    applyDiff(changes, "folder", diffFolder(form, baseline));
    applyDiff(changes, "path", diffPath(form, baseline));
    applyDiff(changes, "scale", diffScale(form, baseline));
    applyDiff(changes, "origin", diffOrigin(form, baseline));
    if (form.originMarker !== baseline.originMarker) {
        changes.originMarker = form.originMarker ? true : undefined;
    }
    applyDiff(changes, "namePattern", diffNamePattern(form, baseline));
    return changes;
}

interface TagDetailsProps {
    indentPx: number;
    node: TagTreeNode;
    busy: boolean;
    onChange: (changes: Partial<TagBag>) => void;
}

export const TagDetails: React.FC<TagDetailsProps> = ({ indentPx, node, busy, onChange }) => {
    const baseline = React.useMemo(() => formFromTags(node.tags), [node.tags]);
    const [form, setForm] = React.useState<DetailForm>(baseline);
    const lastRawName = React.useRef(node.rawName);

    React.useEffect(() => {
        if (lastRawName.current !== node.rawName) {
            lastRawName.current = node.rawName;
            setForm(formFromTags(node.tags));
        }
    }, [node.rawName, node.tags]);

    const dirty = !formsEqual(form, baseline);

    const setField = React.useCallback(<K extends keyof DetailForm>(key: K, value: DetailForm[K]) => {
        setForm((prev) => ({ ...prev, [key]: value }));
    }, []);

    const onApply = React.useCallback(() => {
        const changes = computeChanges(form, baseline);
        log.debug("TagsSection.details", "apply", node.layerPath, changes);
        if (Object.keys(changes).length > 0) onChange(changes);
    }, [form, baseline, node.layerPath, onChange]);

    const onRevert = React.useCallback(() => {
        setForm(baseline);
    }, [baseline]);

    const onFolder = React.useCallback(
        (e: React.SyntheticEvent) => setField("folder", (e.target as HTMLInputElement).value),
        [setField],
    );
    const onPath = React.useCallback(
        (e: React.SyntheticEvent) => setField("path", (e.target as HTMLInputElement).value),
        [setField],
    );
    const onScale = React.useCallback(
        (e: React.SyntheticEvent) => setField("scale", (e.target as HTMLInputElement).value),
        [setField],
    );
    const onOriginX = React.useCallback(
        (e: React.SyntheticEvent) => setField("originX", (e.target as HTMLInputElement).value),
        [setField],
    );
    const onOriginY = React.useCallback(
        (e: React.SyntheticEvent) => setField("originY", (e.target as HTMLInputElement).value),
        [setField],
    );
    const onOriginMarker = React.useCallback(
        (e: React.SyntheticEvent) => setField("originMarker", (e.target as HTMLInputElement).checked),
        [setField],
    );
    const onNamePattern = React.useCallback(
        (e: React.SyntheticEvent) => setField("namePattern", (e.target as HTMLInputElement).value),
        [setField],
    );

    const onUseSelection = React.useCallback(() => {
        const center = readSelectionCenter();
        if (center === null) {
            log.warn("TagsSection.details", "use-selection: no marquee selection bounds");
            return;
        }
        log.debug("TagsSection.details", "use-selection", center);
        setForm((prev) => ({
            ...prev,
            originX: String(center.x),
            originY: String(center.y),
        }));
    }, []);

    return (
        <div className="tag-details" style={{ paddingLeft: `${indentPx + 18}px` }}>
            <DetailRow label="folder" hint="[folder:NAME] - output subfolder under images/">
                <input
                    type="text"
                    className="tag-input"
                    value={form.folder}
                    placeholder="(none)"
                    disabled={busy}
                    onChange={onFolder}
                />
            </DetailRow>
            <DetailRow label="path" hint="[path:NAME] - filename stem override (no slashes)">
                <input
                    type="text"
                    className="tag-input"
                    value={form.path}
                    placeholder="(layer name)"
                    disabled={busy}
                    onChange={onPath}
                />
            </DetailRow>
            <DetailRow label="scale" hint="[scale:N] - pre-export bounds multiplier (>0)">
                <input
                    type="text"
                    className="tag-input"
                    value={form.scale}
                    placeholder="1"
                    disabled={busy}
                    onChange={onScale}
                />
            </DetailRow>
            <DetailRow label="origin" hint="[origin:X,Y] - explicit pivot in PSD pixels">
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originX}
                    placeholder="x"
                    disabled={busy}
                    onChange={onOriginX}
                />
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originY}
                    placeholder="y"
                    disabled={busy}
                    onChange={onOriginY}
                />
                <sp-action-button
                    onClick={onUseSelection}
                    disabled={busy ? true : undefined}
                    title="Fill X / Y from the centre of the current Photoshop marquee selection"
                >
                    From selection
                </sp-action-button>
            </DetailRow>
            <DetailRow label="origin marker" hint="[origin] - layer's bbox centre = parent group's pivot">
                <input
                    type="checkbox"
                    checked={form.originMarker}
                    disabled={busy}
                    onChange={onOriginMarker}
                />
            </DetailRow>
            {node.isGroup && (
                <DetailRow label="name pattern" hint="[name:PRE*SUF] - rewrites group children names; * = original">
                    <input
                        type="text"
                        className="tag-input"
                        value={form.namePattern}
                        placeholder="(none)"
                        disabled={busy}
                        onChange={onNamePattern}
                    />
                </DetailRow>
            )}
            <div className="tag-detail-actions">
                <sp-action-button onClick={onRevert} disabled={!dirty || busy ? true : undefined}>
                    Revert
                </sp-action-button>
                <sp-action-button onClick={onApply} disabled={!dirty || busy ? true : undefined}>
                    Apply
                </sp-action-button>
            </div>
        </div>
    );
};

const DetailRow: React.FC<{
    label: string;
    hint: string;
    children: React.ReactNode;
}> = ({ label, hint, children }) => (
    <div className="tag-detail-row" title={hint}>
        <span className="tag-detail-label">{label}</span>
        <span className="tag-detail-controls">{children}</span>
    </div>
);
