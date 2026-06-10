// Tags panel: the layer tree with bracket-tag controls plus the
// selected entry's reveal-output detail.

import React from "react";

import type { ExportOptions } from "../lib/planner";
import { useActiveLayerPath } from "../hooks/useActiveLayerPath";
import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFilenameTemplate } from "../hooks/useFilenameTemplate";
import { useFolderCache } from "../hooks/useFolderCache";
import { useTagTree } from "../hooks/useTagTree";
import { collapseKey } from "../utils/collapse-key";
import { DocSection } from "./sections/DocSection";
import { RevealOutputSection } from "./sections/RevealOutputSection";
import { TagsSection } from "./sections/TagsSection";

export const ProscenioTagsPanel: React.FC = () => {
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const version = useDocumentChanges();
    const activeLayerPath = useActiveLayerPath(version);
    const tags = useTagTree(version);
    const preview = useExportPreview();
    const templates = useFilenameTemplate();
    const { folder } = useFolderCache();
    const [collapsed, setCollapsed] = React.useState<ReadonlySet<string>>(() => new Set());

    const opts = React.useMemo<ExportOptions>(
        () => ({
            skipHidden: true,
            polygonTemplate: templates.polygonTemplate,
            framesTemplate: templates.framesTemplate,
        }),
        [templates.polygonTemplate, templates.framesTemplate],
    );

    React.useEffect(() => {
        void refreshDoc();
        preview.refresh(opts);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version, opts]);

    const renameFn = tags.rename;
    const onRename = React.useCallback(
        (layerPath: readonly string[], newName: string) => {
            void renameFn(layerPath, newName);
        },
        [renameFn],
    );

    const onToggleCollapse = React.useCallback((displayPath: readonly string[]) => {
        const key = collapseKey(displayPath);
        setCollapsed((prev) => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    }, []);

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={() => { void refreshDoc(); }} />
            <TagsSection
                tree={tags.tree}
                activeLayerPath={activeLayerPath}
                collapsed={collapsed}
                busy={tags.busy}
                lastError={tags.lastError}
                onRename={onRename}
                onToggleCollapse={onToggleCollapse}
            />
            <RevealOutputSection
                preview={preview.preview}
                activeLayerPath={activeLayerPath}
                folder={folder}
            />
        </div>
    );
};
