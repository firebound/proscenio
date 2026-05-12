// Proscenio main panel. Pure composition: each section owns its own
// presentation, each hook owns its own state. The panel only wires
// them together. Adding a new section (e.g. SPEC 011 tag inspector)
// means adding one hook + one section component, not editing this
// file.

import React from "react";

import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useExportFlow } from "../hooks/useExportFlow";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFolderCache } from "../hooks/useFolderCache";
import { useImportFlow } from "../hooks/useImportFlow";
import { DebugSection } from "./sections/DebugSection";
import { DocSection } from "./sections/DocSection";
import { ExportSection } from "./sections/ExportSection";
import { FolderSection } from "./sections/FolderSection";
import { ImportSection } from "./sections/ImportSection";

export const ProscenioExporter: React.FC = () => {
    const { folder, pick: pickFolder, clear: clearFolder } = useFolderCache();
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const exportFlow = useExportFlow();
    const importFlow = useImportFlow();
    const preview = useExportPreview();

    const exportDisabled = exportFlow.busy || folder === null || doc === null;

    const onExport = React.useCallback(() => {
        if (folder !== null) void exportFlow.run(folder);
    }, [exportFlow, folder]);

    const onRefreshPreview = React.useCallback(() => {
        preview.refresh(exportFlow.opts);
    }, [preview, exportFlow.opts]);

    // Auto-refresh the preview when the panel mounts and whenever the
    // export options change. Live PS-event subscription (layer add /
    // rename / delete) is parked for Wave 11.3 - until then the artist
    // hits the Doc-section Refresh button after editing the PSD and
    // both the doc snapshot AND this preview rerun.
    React.useEffect(() => {
        preview.refresh(exportFlow.opts);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [exportFlow.opts, doc]);

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={refreshDoc} />
            <FolderSection folder={folder} onPick={pickFolder} onClear={clearFolder} />
            <ExportSection
                opts={exportFlow.opts}
                busy={exportFlow.busy}
                disabled={exportDisabled}
                last={exportFlow.last}
                onToggleOption={exportFlow.setOption}
                onExport={onExport}
            />
            <ImportSection
                busy={importFlow.busy}
                last={importFlow.last}
                manifestErrors={importFlow.manifestErrors}
                onImport={importFlow.run}
            />
            <DebugSection preview={preview.preview} onRefresh={onRefreshPreview} />
        </div>
    );
};
