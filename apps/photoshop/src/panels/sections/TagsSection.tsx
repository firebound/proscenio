// Thin container for the Tags tab. Walks the planner-built tree and
// hands each node to `TagRow`. Real work lives under `./tags/`.

import React from "react";

import type { TagTreeNode } from "../../domain/tag-tree";
import { elementsEqual } from "../../util/arrays";
import { collapseKey } from "../../util/collapseKey";
import { Accordion } from "../common/Accordion";
import { TagRow } from "./tags/Row";

interface Props {
    tree: TagTreeNode[];
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    lastError: string | null;
    onRename: (layerPath: readonly string[], newName: string) => void;
    onToggleCollapse: (displayPath: readonly string[]) => void;
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
            <Accordion title="Tags">
                <sp-body size="XS" className="muted">No layers. Open a PSD to begin tagging.</sp-body>
            </Accordion>
        );
    }
    return (
        <Accordion
            title="Tags"
            badge={String(tree.length)}
            hint="Layer tree with bracket-tag controls per row. Click + on a row to edit folder / path / scale / origin / name pattern."
        >
            {lastError !== null && (
                <sp-body size="XS" className="result-row warn">{lastError}</sp-body>
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
        </Accordion>
    );
};

interface NodeListProps {
    nodes: TagTreeNode[];
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    onRename: Props["onRename"];
    onToggleCollapse: Props["onToggleCollapse"];
}

const TagNodeList: React.FC<NodeListProps> = ({
    nodes,
    activeLayerPath,
    collapsed,
    busy,
    onRename,
    onToggleCollapse,
}) => (
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

interface BranchProps {
    node: TagTreeNode;
    activeLayerPath: readonly string[] | null;
    collapsed: ReadonlySet<string>;
    busy: boolean;
    onRename: Props["onRename"];
    onToggleCollapse: Props["onToggleCollapse"];
}

const TagNodeBranch: React.FC<BranchProps> = ({
    node,
    activeLayerPath,
    collapsed,
    busy,
    onRename,
    onToggleCollapse,
}) => {
    const selected = activeLayerPath !== null
        && elementsEqual(node.layerPath, activeLayerPath);
    const key = collapseKey(node.displayPath);
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

export { writeLayerName } from "../../domain/tag-writer";
