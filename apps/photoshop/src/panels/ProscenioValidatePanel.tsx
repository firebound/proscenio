// SPEC 011 Wave 11.4: dedicated Validate panel. Lives next to the
// Tags / Debug / Exporter panels so the artist can keep warnings +
// skipped layers visible while editing tags or running the export.
// Shares the same `useExportPreview` polling pipeline; nothing here
// duplicates state.

import React from "react";

import type { ExportOptions } from "../domain/planner";
import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFilenameTemplate } from "../hooks/useFilenameTemplate";
import { DocSection } from "./sections/DocSection";
import { ValidateSection } from "./sections/ValidateSection";

export const ProscenioValidatePanel: React.FC = () => {
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const preview = useExportPreview();
    const templates = useFilenameTemplate();
    const version = useDocumentChanges();

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

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={refreshDoc} />
            <ValidateSection preview={preview.preview} />
        </div>
    );
};
