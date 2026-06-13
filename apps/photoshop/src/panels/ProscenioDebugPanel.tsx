// Standalone debug / preview panel: dry-run preview plus the active
// layer's matching manifest row.

import React from "react";

import type { ExportOptions } from "../lib/planner";
import { useActiveLayerPath } from "../hooks/useActiveLayerPath";
import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFilenameTemplate } from "../hooks/useFilenameTemplate";
import { DebugSection } from "./sections/DebugSection";
import { DocSection } from "./sections/DocSection";
import { LogLevelSection } from "./sections/LogLevelSection";

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
            <DocSection doc={doc} onRefresh={() => { void refreshDoc(); }} />
            <DebugSection
                preview={preview.preview}
                activeLayerPath={activeLayerPath}
                onRefresh={onRefresh}
            />
            <LogLevelSection />
        </div>
    );
};
