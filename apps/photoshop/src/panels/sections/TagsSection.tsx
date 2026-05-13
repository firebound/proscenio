import React from "react";

import type { BlendMode } from "../../domain/manifest";
import type { TagBag } from "../../domain/tag-parser";
import type { TagTreeNode } from "../../domain/tag-tree";
import {
    applyTagChanges,
    setBlendTag,
    setKindTag,
    toggleTag,
} from "../../domain/tag-writer";
import { selectLayerByPath } from "../../io/ps-selection";
import { log } from "../../util/log";

// UXP's Adobe Clean font does not render most Unicode geometric
// shapes, so we use pure ASCII chars. Each glyph is one column-aligned
// monospace letter wrapped in a `<button title=...>` for tooltip
// readability.
const GLYPH_OPEN = "v";
const GLYPH_CLOSED = ">";
const GLYPH_IGNORE = "X";
const GLYPH_MERGE = "M";
const GLYPH_EXPAND = "+";
const GLYPH_COLLAPSE = "-";

interface Props {
    tree: TagTreeNode[];
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    lastError: string | null;
    onRename: (layerPath: readonly string[], newName: string) => void;
    onToggleCollapse: (layerPath: readonly string[]) => void;
}

export const TagsSection: React.FC<Props> = ({
    tree,
    activeLayerPath,
    collapsed,
    busy,
    lastError,
    onRename,
    onToggleCollapse,
}) => {
    if (tree.length === 0) {
        return (
            <section className="section">
                <sp-heading size="XS">Tags</sp-heading>
                <sp-body size="XS" className="muted">
                    No layers. Open a PSD to begin tagging.
                </sp-body>
            </section>
        );
    }
    return (
        <section className="section">
            <sp-heading size="XS">Tags</sp-heading>
            {lastError !== null && (
                <sp-body size="XS" className="result-row warn">
                    {lastError}
                </sp-body>
            )}
            <div className="tag-tree">
                <TagNodeList
                    nodes={tree}
                    activeLayerPath={activeLayerPath}
                    collapsed={collapsed}
                    busy={busy}
                    onRename={onRename}
                    onToggleCollapse={onToggleCollapse}
                />
            </div>
        </section>
    );
};

const TagNodeList: React.FC<{
    nodes: TagTreeNode[];
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    onRename: Props["onRename"];
    onToggleCollapse: Props["onToggleCollapse"];
}> = ({ nodes, activeLayerPath, collapsed, busy, onRename, onToggleCollapse }) => (
    <>
        {nodes.map((node) => (
            <TagNodeBranch
                key={node.layerPath.join("/")}
                node={node}
                activeLayerPath={activeLayerPath}
                collapsed={collapsed}
                busy={busy}
                onRename={onRename}
                onToggleCollapse={onToggleCollapse}
            />
        ))}
    </>
);

const TagNodeBranch: React.FC<{
    node: TagTreeNode;
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    onRename: Props["onRename"];
    onToggleCollapse: Props["onToggleCollapse"];
}> = ({
    node,
    activeLayerPath,
    collapsed,
    busy,
    onRename,
    onToggleCollapse,
}) => {
    const selected = pathsEqual(node.layerPath, activeLayerPath);
    const key = node.displayPath.join("/");
    const isCollapsed = collapsed.has(key);
    const showChildren = node.children.length > 0 && !isCollapsed;
    return (
        <>
            <TagRow
                node={node}
                selected={selected}
                collapsed={isCollapsed}
                busy={busy}
                onRename={onRename}
                onToggleCollapse={onToggleCollapse}
            />
            {showChildren && (
                <TagNodeList
                    nodes={node.children}
                    activeLayerPath={activeLayerPath}
                    collapsed={collapsed}
                    busy={busy}
                    onRename={onRename}
                    onToggleCollapse={onToggleCollapse}
                />
            )}
        </>
    );
};

interface TagRowProps {
    node: TagTreeNode;
    selected: boolean;
    collapsed: boolean;
    busy: boolean;
    onRename: Props["onRename"];
    onToggleCollapse: Props["onToggleCollapse"];
}

const TagRowImpl: React.FC<TagRowProps> = ({
    node,
    selected,
    collapsed,
    busy,
    onRename,
    onToggleCollapse,
}) => {
    // Local expand state - keeps the click confined to this row, so
    // toggling the `+` does not re-render the entire tree. Resets
    // when React unmounts the row (rename / tree shape change).
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

    const rowClass = [
        "tag-row",
        selected ? "selected" : "",
        node.tags.ignore === true ? "ignored" : "",
        node.visible ? "" : "hidden",
    ]
        .filter((s) => s.length > 0)
        .join(" ");
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

const ClickSpan: React.FC<{
    className: string;
    title: string;
    disabled: boolean;
    onClick: () => void;
    children: React.ReactNode;
}> = ({ className, title, disabled, onClick, children }) => {
    const handleClick = React.useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            if (!disabled) onClick();
        },
        [disabled, onClick],
    );
    const handleKey = React.useCallback(
        (e: React.KeyboardEvent) => {
            if (disabled) return;
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
            }
        },
        [disabled, onClick],
    );
    // NOTE: native <button> elements do not render text content in
    // UXP's mini-DOM (verified visually - the text is blank inside
    // <button>X</button>). Spans render text reliably, so we use
    // role="button" + onKeyDown to keep keyboard semantics intact.
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions, jsx-a11y/no-noninteractive-element-interactions
    return (
        <span
            className={className}
            role="button"
            tabIndex={disabled ? -1 : 0}
            title={title}
            onClick={handleClick}
            onKeyDown={handleKey}
        >
            {children}
        </span>
    );
};

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

const TagDetails: React.FC<{
    indentPx: number;
    node: TagTreeNode;
    busy: boolean;
    onChange: (changes: Partial<TagBag>) => void;
}> = ({ indentPx, node, busy, onChange }) => {
    // Local draft state so typing in a field does not trigger a
    // rename on every blur. Apply commits all dirty fields in one
    // rename call; Revert restores the baseline.
    const baseline = React.useMemo(() => formFromTags(node.tags), [node.tags]);
    const [form, setForm] = React.useState<DetailForm>(baseline);
    const lastRawName = React.useRef(node.rawName);

    // External rename (toggle X clicked, etc.) updates node.rawName.
    // Re-sync the form from the new tags so the panel keeps showing
    // the truth on disk.
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
        const changes: Partial<TagBag> = {};
        // folder
        const f = form.folder.trim();
        if (f !== (baseline.folder.trim())) changes.folder = f.length === 0 ? undefined : f;
        // path - same parser-side validation as the live name parser
        const p = form.path.trim();
        if (p !== baseline.path.trim()) {
            if (p.length === 0) changes.path = undefined;
            else if (!p.includes("/") && !p.includes("\\") && p !== "." && p !== "..") {
                changes.path = p;
            }
        }
        // scale - positive numeric only
        const s = form.scale.trim();
        if (s !== baseline.scale.trim()) {
            if (s.length === 0) changes.scale = undefined;
            else if (/^(?:\d+\.?\d*|\.\d+)$/.test(s)) {
                const n = Number(s);
                if (Number.isFinite(n) && n > 0) changes.scale = n;
            }
        }
        // origin pair - both blank clears, both numeric sets
        const ox = form.originX.trim();
        const oy = form.originY.trim();
        const baseX = baseline.originX.trim();
        const baseY = baseline.originY.trim();
        if (ox !== baseX || oy !== baseY) {
            if (ox.length === 0 && oy.length === 0) changes.origin = undefined;
            else {
                const x = Number.parseFloat(ox);
                const y = Number.parseFloat(oy);
                if (Number.isFinite(x) && Number.isFinite(y)) changes.origin = [x, y];
            }
        }
        // origin marker
        if (form.originMarker !== baseline.originMarker) {
            changes.originMarker = form.originMarker ? true : undefined;
        }
        // name pattern - must contain *
        const np = form.namePattern.trim();
        if (np !== baseline.namePattern.trim()) {
            if (np.length === 0) changes.namePattern = undefined;
            else if (np.includes("*")) changes.namePattern = np;
        }
        log.debug("TagsSection.details", "apply", node.layerPath, changes);
        if (Object.keys(changes).length > 0) onChange(changes);
    }, [form, baseline, node.layerPath, onChange]);

    const onRevert = React.useCallback(() => {
        setForm(baseline);
    }, [baseline]);

    return (
        <div className="tag-details" style={{ paddingLeft: `${indentPx + 18}px` }}>
            <DetailRow label="folder" hint="[folder:NAME] - output subfolder under images/">
                <input
                    type="text"
                    className="tag-input"
                    value={form.folder}
                    placeholder="(none)"
                    disabled={busy}
                    onChange={(e) => setField("folder", (e.target as HTMLInputElement).value)}
                />
            </DetailRow>
            <DetailRow label="path" hint="[path:NAME] - filename stem override (no slashes)">
                <input
                    type="text"
                    className="tag-input"
                    value={form.path}
                    placeholder="(layer name)"
                    disabled={busy}
                    onChange={(e) => setField("path", (e.target as HTMLInputElement).value)}
                />
            </DetailRow>
            <DetailRow label="scale" hint="[scale:N] - pre-export bounds multiplier (>0)">
                <input
                    type="text"
                    className="tag-input"
                    value={form.scale}
                    placeholder="1"
                    disabled={busy}
                    onChange={(e) => setField("scale", (e.target as HTMLInputElement).value)}
                />
            </DetailRow>
            <DetailRow label="origin" hint="[origin:X,Y] - explicit pivot in PSD pixels">
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originX}
                    placeholder="x"
                    disabled={busy}
                    onChange={(e) => setField("originX", (e.target as HTMLInputElement).value)}
                />
                <input
                    type="text"
                    className="tag-input narrow"
                    value={form.originY}
                    placeholder="y"
                    disabled={busy}
                    onChange={(e) => setField("originY", (e.target as HTMLInputElement).value)}
                />
            </DetailRow>
            <DetailRow label="origin marker" hint="[origin] - layer's bbox centre = parent group's pivot">
                <input
                    type="checkbox"
                    checked={form.originMarker}
                    disabled={busy}
                    onChange={(e) => setField("originMarker", (e.target as HTMLInputElement).checked)}
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
                        onChange={(e) => setField("namePattern", (e.target as HTMLInputElement).value)}
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

const TagRow = React.memo(TagRowImpl, tagRowEqual);

const GlyphToggle: React.FC<{
    glyph: string;
    title: string;
    active: boolean;
    disabled: boolean;
    onClick: () => void;
}> = ({ glyph, title, active, disabled, onClick }) => {
    const className = `tag-toggle${active ? " active" : ""}${disabled ? " disabled" : ""}`;
    return (
        <ClickSpan className={className} title={title} disabled={disabled} onClick={onClick}>
            {glyph}
        </ClickSpan>
    );
};

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

function hasBadge(tags: TagBag): boolean {
    return (
        tags.folder !== undefined
        || tags.path !== undefined
        || tags.scale !== undefined
        || tags.origin !== undefined
        || tags.originMarker === true
        || tags.namePattern !== undefined
    );
}

const BadgeStrip: React.FC<{ tags: TagBag }> = ({ tags }) => (
    <>
        {tags.folder !== undefined && <Badge label="F" value={tags.folder} title={`folder: ${tags.folder}`} />}
        {tags.path !== undefined && <Badge label="P" value={tags.path} title={`path: ${tags.path}`} />}
        {tags.scale !== undefined && <Badge label="S" value={String(tags.scale)} title={`scale: ${tags.scale}`} />}
        {tags.origin !== undefined && (
            <Badge
                label="O"
                value={`${tags.origin[0]},${tags.origin[1]}`}
                title={`origin: ${tags.origin[0]}, ${tags.origin[1]} px`}
            />
        )}
        {tags.originMarker === true && (
            <Badge label="OM" value="" title="origin marker - bbox centre used as parent's pivot" />
        )}
        {tags.namePattern !== undefined && (
            <Badge label="NP" value={tags.namePattern} title={`name pattern: ${tags.namePattern}`} />
        )}
    </>
);

const Badge: React.FC<{ label: string; value: string; title: string }> = ({ label, value, title }) => (
    <span className="tag-badge" title={title}>
        <span className="tag-badge-label">{label}</span>
        <span className="tag-badge-value">{value}</span>
    </span>
);

function pathsEqual(a: readonly string[], b: readonly string[] | null): boolean {
    if (b === null) return false;
    if (a === b) return true;
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

export { writeLayerName } from "../../domain/tag-writer";
