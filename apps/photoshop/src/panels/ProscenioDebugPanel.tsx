// Standalone debug / preview panel. Mirrors the export flow's
// dry-run but in its own dockable / floatable window so the artist
// can keep the live entry + skipped list visible while the main
// exporter panel stays narrow.
//
// Templates are read from `useFilenameTemplate` (shared via
// localStorage with the exporter panel), so the dry-run paths
// always match what the exporter would write. The active PS layer
// chain feeds reveal-output: the matching manifest row is highlighted
// in `DebugSection`.

import React from "react";

import type { ExportOptions } from "../domain/planner";
import { useActiveLayerPath } from "../hooks/useActiveLayerPath";
import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFilenameTemplate } from "../hooks/useFilenameTemplate";
import { DebugSection } from "./sections/DebugSection";
import { DocSection } from "./sections/DocSection";

export const ProscenioDebugPanel: React.FC = () => {
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const preview = useExportPreview();
    const templates = useFilenameTemplate();
    const version = useDocumentChanges();
    const activeLayerPath = useActiveLayerPath(version);

    const opts = React.useMemo<ExportOptions>(
        () => ({
            skipHidden: true,
            polygonTemplate: templates.polygonTemplate,
            framesTemplate: templates.framesTemplate,
        }),
        [templates.polygonTemplate, templates.framesTemplate],
    );

    const onRefresh = React.useCallback(() => {
        preview.refresh(opts);
    }, [preview, opts]);

    React.useEffect(() => {
        void refreshDoc();
        preview.refresh(opts);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version, opts]);

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={refreshDoc} />
            <DebugSection
                preview={preview.preview}
                activeLayerPath={activeLayerPath}
                onRefresh={onRefresh}
            />
        </div>
    );
};
