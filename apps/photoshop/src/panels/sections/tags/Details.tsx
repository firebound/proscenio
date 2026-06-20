// Advanced tag-fields panel (the `+` expander on each row).
//
// Inputs are a LOCAL draft: typing does not commit. Apply computes the
// delta vs the baseline (node.tags) and fires one rename; an external
// rename resets the form to the on-disk truth.

import React from "react";

import type { TagTreeNode } from "../../../lib/tag-tree";
import {
    computeChanges,
    detailFormErrors,
    formFromTags,
    formsEqual,
    type DetailForm,
    type TagChanges,
} from "../../../lib/tag-form";
import { readSelectionCenter } from "../../../api/ps-selection-bounds";
import { log } from "../../../utils/log";

interface TagDetailsProps {
    indentPx: number;
    node: TagTreeNode;
    onChange: (changes: TagChanges) => void;
}

export const TagDetails: React.FC<TagDetailsProps> = ({ indentPx, node, onChange }) => {
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
    // Fields whose typed value the parser would reject. computeChanges
    // silently SKIPs these, so without surfacing them the artist sees the
    // value sitting in the box yet Apply writes nothing. Block Apply and
    // mark the offending rows instead.
    const errors = React.useMemo(() => detailFormErrors(form), [form]);
    const hasErrors = Object.keys(errors).length > 0;

    const setField = React.useCallback(<K extends keyof DetailForm>(key: K, value: DetailForm[K]) => {
        setForm((prev) => ({ ...prev, [key]: value }));
    }, []);

    const onApply = React.useCallback(() => {
        const changes = computeChanges(form, baseline);
        log.debug("TagsSection.details", "apply", node.layerPath, changes);
        if (Object.keys(changes.set).length > 0 || changes.clear.length > 0) onChange(changes);
    }, [form, baseline, node.layerPath, onChange]);

    const onRevert = React.useCallback(() => {
        setForm(baseline);
    }, [baseline]);

    const onFolder = React.useCallback(
        (e: React.SyntheticEvent) => { setField("folder", (e.target as HTMLInputElement).value); },
        [setField],
    );
    const onPath = React.useCallback(
        (e: React.SyntheticEvent) => { setField("path", (e.target as HTMLInputElement).value); },
        [setField],
    );
    const onScale = React.useCallback(
        (e: React.SyntheticEvent) => { setField("scale", (e.target as HTMLInputElement).value); },
        [setField],
    );
    const onOriginX = React.useCallback(
        (e: React.SyntheticEvent) => { setField("originX", (e.target as HTMLInputElement).value); },
        [setField],
    );
    const onOriginY = React.useCallback(
        (e: React.SyntheticEvent) => { setField("originY", (e.target as HTMLInputElement).value); },
        [setField],
    );
    const onOriginMarker = React.useCallback(
        (e: React.SyntheticEvent) => { setField("originMarker", (e.target as HTMLInputElement).checked); },
        [setField],
    );
    const onNamePattern = React.useCallback(
        (e: React.SyntheticEvent) => { setField("namePattern", (e.target as HTMLInputElement).value); },
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
                    onChange={onFolder}
                />
            </DetailRow>
            <DetailRow label="path" hint="[path:NAME] - filename stem override (no slashes)" error={errors.path}>
                <input
                    type="text"
                    className="tag-input"
                    value={form.path}
                    placeholder="(layer name)"
                    onChange={onPath}
                />
            </DetailRow>
            <DetailRow label="scale" hint="[scale:N] - pre-export bounds multiplier (>0)" error={errors.scale}>
                <input
                    type="text"
                    className="tag-input"
                    value={form.scale}
                    placeholder="1"
                    onChange={onScale}
                />
            </DetailRow>
            <DetailRow label="origin" hint="[origin:X,Y] - explicit pivot in PSD pixels" error={errors.origin}>
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originX}
                    placeholder="x"
                    onChange={onOriginX}
                />
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originY}
                    placeholder="y"
                    onChange={onOriginY}
                />
                <sp-action-button
                    onClick={onUseSelection}
                    title="Fill X / Y from the centre of the current Photoshop marquee selection"
                >
                    From selection
                </sp-action-button>
            </DetailRow>
            <DetailRow label="origin marker" hint="[origin] - layer's bbox centre = parent group's pivot">
                <input
                    type="checkbox"
                    checked={form.originMarker}
                    onChange={onOriginMarker}
                />
            </DetailRow>
            {node.isGroup && (
                <DetailRow label="name pattern" hint="[name:PRE*SUF] - rewrites group children names; * = original" error={errors.namePattern}>
                    <input
                        type="text"
                        className="tag-input"
                        value={form.namePattern}
                        placeholder="(none)"
                        onChange={onNamePattern}
                    />
                </DetailRow>
            )}
            <div className="tag-detail-actions">
                <sp-action-button onClick={onRevert} disabled={!dirty ? true : undefined}>
                    Revert
                </sp-action-button>
                <sp-action-button onClick={onApply} disabled={!dirty || hasErrors ? true : undefined}>
                    Apply
                </sp-action-button>
            </div>
        </div>
    );
};

const DetailRow: React.FC<{
    label: string;
    hint: string;
    error?: string | undefined;
    children: React.ReactNode;
}> = ({ label, hint, error, children }) => (
    <div className={error === undefined ? "tag-detail-row" : "tag-detail-row has-error"} title={hint}>
        <span className="tag-detail-label">{label}</span>
        <span className="tag-detail-controls">{children}</span>
        {error !== undefined && <span className="tag-detail-error" role="alert">{error}</span>}
    </div>
);
