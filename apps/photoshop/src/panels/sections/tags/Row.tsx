// One row of the Tags panel. Wraps `TagRowImpl` in `React.memo` with
// a structural equality check that short-circuits on node reference
// equality (preserved across polls by `buildTagTreeReusing`).

import React from "react";

import type { BlendMode } from "../../../domain/manifest";
import type { TagBag } from "../../../domain/tag-parser";
import type { TagTreeNode } from "../../../domain/tag-tree";
import {
    applyTagChanges,
    setBlendTag,
    setKindTag,
    toggleTag,
} from "../../../domain/tag-writer";
import { selectLayerByPath } from "../../../io/ps-selection";
import { log } from "../../../util/log";
import { BadgeStrip, hasBadge } from "./Badges";
import { TagDetails } from "./Details";
import {
    ClickSpan,
    GLYPH_CLOSED,
    GLYPH_COLLAPSE,
    GLYPH_EXPAND,
    GLYPH_IGNORE,
    GLYPH_MERGE,
    GLYPH_OPEN,
    GlyphToggle,
} from "./primitives";

export interface TagRowProps {
    node: TagTreeNode;
    selected: boolean;
    collapsed: boolean;
    busy: boolean;
    onRename: (layerPath: readonly string[], newName: string) => void;
    onToggleCollapse: (displayPath: readonly string[]) => void;
}

const TagRowImpl: React.FC<TagRowProps> = ({
    node,
    selected,
    collapsed,
    busy,
    onRename,
    onToggleCollapse,
}) => {
    const [expanded, setExpanded] = React.useState(false);

    const onClickName = React.useCallback(() => {
        log.debug("TagsSection", "select", node.layerPath);
        void selectLayerByPath(node.layerPath);
    }, [node.layerPath]);

    const onClickDisclosure = React.useCallback(() => {
        if (node.isGroup) onToggleCollapse(node.displayPath);
    }, [node.isGroup, node.displayPath, onToggleCollapse]);

    const onToggleIgnore = React.useCallback(() => {
        const next = node.tags.ignore !== true;
        const newName = toggleTag(node.displayName, node.tags, "ignore", next);
        log.debug("TagsSection", "ignore", node.layerPath, next, newName);
        onRename(node.layerPath, newName);
    }, [node.layerPath, node.displayName, node.tags, onRename]);

    const onToggleMerge = React.useCallback(() => {
        const next = node.tags.merge !== true;
        const newName = toggleTag(node.displayName, node.tags, "merge", next);
        log.debug("TagsSection", "merge", node.layerPath, next, newName);
        onRename(node.layerPath, newName);
    }, [node.layerPath, node.displayName, node.tags, onRename]);

    const onKindChange = React.useCallback(
        (e: React.SyntheticEvent) => {
            const value = (e.target as HTMLSelectElement).value;
            const kind = parseKind(value);
            const newName = setKindTag(node.displayName, node.tags, kind);
            log.debug("TagsSection", "kind", node.layerPath, kind, newName);
            onRename(node.layerPath, newName);
        },
        [node.layerPath, node.displayName, node.tags, onRename],
    );

    const onBlendChange = React.useCallback(
        (e: React.SyntheticEvent) => {
            const value = (e.target as HTMLSelectElement).value;
            const blend = parseBlend(value);
            const newName = setBlendTag(node.displayName, node.tags, blend);
            log.debug("TagsSection", "blend", node.layerPath, blend, newName);
            onRename(node.layerPath, newName);
        },
        [node.layerPath, node.displayName, node.tags, onRename],
    );

    const onClickExpand = React.useCallback(() => {
        setExpanded((prev) => !prev);
    }, []);

    const onAdvancedChange = React.useCallback(
        (changes: Partial<TagBag>) => {
            const newName = applyTagChanges(node.displayName, node.tags, changes);
            log.debug("TagsSection", "advanced", node.layerPath, changes, newName);
            onRename(node.layerPath, newName);
        },
        [node.layerPath, node.displayName, node.tags, onRename],
    );

    const rowClass = buildRowClass(selected, node.tags.ignore === true, !node.visible);
    const indentPx = node.depth * 10;
    const labelText = node.displayName.length === 0 ? node.rawName : node.displayName;
    const disclosureGlyph = disclosureGlyphFor(node.isGroup, collapsed);
    const disclosureTitle = disclosureTitleFor(node.isGroup, collapsed);
    const mergeTitle = mergeTitleFor(node.isGroup, node.tags.merge === true);
    const disclosureDisabled = !node.isGroup;

    return (
        <div className={rowClass}>
            <div className="tag-row-header">
                <div className="tag-left" style={{ paddingLeft: `${indentPx}px` }}>
                    <ClickSpan
                        className={`tag-disclosure${disclosureDisabled ? " disabled" : ""}`}
                        title={disclosureTitle}
                        disabled={disclosureDisabled}
                        onClick={onClickDisclosure}
                    >
                        {disclosureGlyph}
                    </ClickSpan>
                    <ClickSpan
                        className="tag-name"
                        title={`Select '${node.rawName}' in Photoshop`}
                        disabled={false}
                        onClick={onClickName}
                    >
                        {labelText}
                    </ClickSpan>
                </div>
                <div className="tag-badges-inline">
                    {hasBadge(node.tags) && <BadgeStrip tags={node.tags} />}
                </div>
                <div className="tag-right">
                    <GlyphToggle
                        glyph={GLYPH_IGNORE}
                        title={node.tags.ignore === true ? "Remove [ignore]" : "Add [ignore] (skip on export)"}
                        active={node.tags.ignore === true}
                        disabled={busy}
                        onClick={onToggleIgnore}
                    />
                    <GlyphToggle
                        glyph={GLYPH_MERGE}
                        title={mergeTitle}
                        active={node.tags.merge === true}
                        disabled={busy || !node.isGroup}
                        onClick={onToggleMerge}
                    />
                    <select
                        key="kind"
                        className="tag-select tag-select-kind"
                        value={node.tags.kind ?? ""}
                        disabled={busy}
                        onChange={onKindChange}
                        title="Kind override - polygon (static quad), mesh (rigged), spritesheet (frames)"
                    >
                        <option key="auto" value="">auto</option>
                        <option key="polygon" value="polygon">poly</option>
                        <option key="mesh" value="mesh">mesh</option>
                        {node.isGroup && <option key="sprite_frame" value="sprite_frame">sprt</option>}
                    </select>
                    <select
                        key="blend"
                        className="tag-select tag-select-blend"
                        value={blendSelectValue(node.tags.blend)}
                        disabled={busy}
                        onChange={onBlendChange}
                        title="Composite blend (none = no [blend] tag written)"
                    >
                        <option key="none" value="none">none</option>
                        <option key="multiply" value="multiply">mult</option>
                        <option key="screen" value="screen">scrn</option>
                        <option key="additive" value="additive">add</option>
                    </select>
                    <GlyphToggle
                        glyph={expanded ? GLYPH_COLLAPSE : GLYPH_EXPAND}
                        title={expanded ? "Hide advanced fields" : "Edit folder / path / scale / origin / name pattern"}
                        active={expanded}
                        disabled={busy}
                        onClick={onClickExpand}
                    />
                </div>
            </div>
            {expanded && (
                <TagDetails
                    indentPx={indentPx}
                    node={node}
                    busy={busy}
                    onChange={onAdvancedChange}
                />
            )}
        </div>
    );
};

export const TagRow = React.memo(TagRowImpl, tagRowEqual);

function tagRowEqual(prev: TagRowProps, next: TagRowProps): boolean {
    // Fast path: when buildTagTreeReusing preserves the node ref,
    // skip the structural walk entirely.
    if (
        prev.node === next.node
        && prev.selected === next.selected
        && prev.collapsed === next.collapsed
        && prev.busy === next.busy
        && prev.onRename === next.onRename
        && prev.onToggleCollapse === next.onToggleCollapse
    ) {
        return true;
    }
    return (
        prev.selected === next.selected
        && prev.collapsed === next.collapsed
        && prev.busy === next.busy
        && prev.onRename === next.onRename
        && prev.onToggleCollapse === next.onToggleCollapse
        && prev.node.rawName === next.node.rawName
        && prev.node.visible === next.node.visible
        && prev.node.depth === next.node.depth
        && prev.node.isGroup === next.node.isGroup
        && tagBagEqual(prev.node.tags, next.node.tags)
    );
}

function tagBagEqual(a: TagBag, b: TagBag): boolean {
    if (a === b) return true;
    return (
        a.ignore === b.ignore
        && a.merge === b.merge
        && a.kind === b.kind
        && a.folder === b.folder
        && a.path === b.path
        && a.blend === b.blend
        && a.scale === b.scale
        && a.originMarker === b.originMarker
        && a.namePattern === b.namePattern
        && originEqual(a.origin, b.origin)
    );
}

function originEqual(
    a: [number, number] | undefined,
    b: [number, number] | undefined,
): boolean {
    if (a === b) return true;
    if (a === undefined || b === undefined) return false;
    return a[0] === b[0] && a[1] === b[1];
}

function buildRowClass(selected: boolean, ignored: boolean, hidden: boolean): string {
    const parts = ["tag-row"];
    if (selected) parts.push("selected");
    if (ignored) parts.push("ignored");
    if (hidden) parts.push("hidden");
    return parts.join(" ");
}

function disclosureGlyphFor(isGroup: boolean, collapsed: boolean): string {
    if (!isGroup) return "";
    return collapsed ? GLYPH_CLOSED : GLYPH_OPEN;
}

function disclosureTitleFor(isGroup: boolean, collapsed: boolean): string {
    if (!isGroup) return "";
    return collapsed ? "Expand group" : "Collapse group";
}

function mergeTitleFor(isGroup: boolean, active: boolean): string {
    if (!isGroup) return "[merge] only applies to groups";
    return active ? "Remove [merge]" : "Add [merge] (flatten group)";
}

function parseKind(value: string): TagBag["kind"] | undefined {
    if (value === "polygon") return "polygon";
    if (value === "mesh") return "mesh";
    if (value === "sprite_frame") return "sprite_frame";
    return undefined;
}

function parseBlend(value: string): BlendMode | undefined {
    if (value === "multiply" || value === "screen" || value === "additive") return value;
    // "none" / "" / "normal" / any unknown -> clear the [blend] tag.
    return undefined;
}

function blendSelectValue(blend: BlendMode | undefined): string {
    if (blend === undefined || blend === "normal") return "none";
    return blend;
}
