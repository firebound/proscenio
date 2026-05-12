// Standalone debug / preview panel. Mirrors the export flow's
// dry-run but in its own dockable / floatable window so the artist
// can keep the live entry + skipped list visible while the main
// exporter panel stays narrow.
//
// The panel uses default export options (`skipHidden: true`); the
// main Exporter panel owns the user-facing toggles. If the artist
// wants a preview with different opts they tweak the Exporter, the
// Debug panel re-runs automatically on next refresh.

import React from "react";

import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportPreview } from "../hooks/useExportPreview";
import { DebugSection } from "./sections/DebugSection";
import { DocSection } from "./sections/DocSection";

const PREVIEW_OPTS = { skipHidden: true };

export const ProscenioDebugPanel: React.FC = () => {
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const preview = useExportPreview();
    const version = useDocumentChanges();

    const onRefresh = React.useCallback(() => {
        preview.refresh(PREVIEW_OPTS);
    }, [preview]);

    // Re-run preview + doc snapshot whenever a PS notification fires
    // (debounced via `useDocumentChanges`). Click-Refresh stays
    // available as a force path.
    React.useEffect(() => {
        void refreshDoc();
        preview.refresh(PREVIEW_OPTS);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version]);

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={refreshDoc} />
            <DebugSection preview={preview.preview} onRefresh={onRefresh} />
        </div>
    );
};
