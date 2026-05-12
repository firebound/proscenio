// Proscenio main panel. Pure composition: each section owns its own
// presentation, each hook owns its own state. The panel only wires
// them together. Adding a new section (e.g. SPEC 011 tag inspector)
// means adding one hook + one section component, not editing this
// file.

import React from "react";

import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportFlow } from "../hooks/useExportFlow";
import { useFolderCache } from "../hooks/useFolderCache";
import { useImportFlow } from "../hooks/useImportFlow";
import { DocSection } from "./sections/DocSection";
import { ExportSection } from "./sections/ExportSection";
import { FolderSection } from "./sections/FolderSection";
import { ImportSection } from "./sections/ImportSection";

export const ProscenioExporter: React.FC = () => {
    const { folder, pick: pickFolder, clear: clearFolder } = useFolderCache();
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const exportFlow = useExportFlow();
    const importFlow = useImportFlow();
    const version = useDocumentChanges();

    // Re-read the active doc whenever PS fires a notification.
    React.useEffect(() => {
        void refreshDoc();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version]);

    const exportDisabled = exportFlow.busy || folder === null || doc === null;

    const onExport = React.useCallback(() => {
        if (folder !== null) void exportFlow.run(folder);
    }, [exportFlow, folder]);

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
        </div>
    );
};
