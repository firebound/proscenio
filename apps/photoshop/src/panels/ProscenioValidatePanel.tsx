// Validate panel: the planner's warnings + skipped layers from a
// live preview run.

import React from "react";

import type { ExportOptions } from "../lib/planner";
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
            <DocSection doc={doc} onRefresh={() => { void refreshDoc(); }} />
            <ValidateSection preview={preview.preview} />
        </div>
    );
};
