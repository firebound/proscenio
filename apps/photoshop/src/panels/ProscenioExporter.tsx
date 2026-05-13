// Proscenio main panel. Pure composition: each section owns its own
// presentation, each hook owns its own state. The panel only wires
// them together. Adding a new section (e.g. SPEC 011 tag inspector)
// means adding one hook + one section component, not editing this
// file.

import React from "react";

import type { ExportOptions } from "../domain/planner";
import { useActiveLayerPath } from "../hooks/useActiveLayerPath";
import { useDocSnapshot } from "../hooks/useDocSnapshot";
import { useDocumentChanges } from "../hooks/useDocumentChanges";
import { useExportFlow } from "../hooks/useExportFlow";
import { useExportPreview } from "../hooks/useExportPreview";
import { useFilenameTemplate } from "../hooks/useFilenameTemplate";
import { useFolderCache } from "../hooks/useFolderCache";
import { useImportFlow } from "../hooks/useImportFlow";
import { useMigration } from "../hooks/useMigration";
import { usePixelsPerUnit } from "../hooks/usePixelsPerUnit";
import { DocSection } from "./sections/DocSection";
import { ExportSection } from "./sections/ExportSection";
import { FolderSection } from "./sections/FolderSection";
import { ImportSection } from "./sections/ImportSection";
import { MigrationSection } from "./sections/MigrationSection";
import { ReexportSection } from "./sections/ReexportSection";

export const ProscenioExporter: React.FC = () => {
    const { folder, pick: pickFolder, clear: clearFolder } = useFolderCache();
    const { doc, refresh: refreshDoc } = useDocSnapshot();
    const exportFlow = useExportFlow();
    const importFlow = useImportFlow();
    const templates = useFilenameTemplate();
    const ppu = usePixelsPerUnit();
    const version = useDocumentChanges();
    const migration = useMigration(version);
    const activeLayerPath = useActiveLayerPath(version);
    const preview = useExportPreview();

    const reexportOpts = React.useMemo<ExportOptions>(
        () => ({
            skipHidden: exportFlow.opts.skipHidden,
            polygonTemplate: templates.polygonTemplate,
            framesTemplate: templates.framesTemplate,
            pixelsPerUnit: ppu.pixelsPerUnit,
        }),
        [
            exportFlow.opts.skipHidden,
            templates.polygonTemplate,
            templates.framesTemplate,
            ppu.pixelsPerUnit,
        ],
    );

    // Push template + pixels-per-unit values into the export options
    // so a single ExportOptions struct is what the controller sees.
    // Depend on the stable `setOption` callback (not the wrapper
    // object) so the effect fires only when values actually change.
    const setOption = exportFlow.setOption;
    React.useEffect(() => {
        setOption("polygonTemplate", templates.polygonTemplate);
        setOption("framesTemplate", templates.framesTemplate);
        setOption("pixelsPerUnit", ppu.pixelsPerUnit);
    }, [setOption, templates.polygonTemplate, templates.framesTemplate, ppu.pixelsPerUnit]);

    // Re-read the active doc + refresh preview whenever PS fires a
    // notification or templates change.
    React.useEffect(() => {
        void refreshDoc();
        preview.refresh(reexportOpts);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [version, reexportOpts]);

    const exportDisabled = exportFlow.busy || folder === null || doc === null;

    const onExport = React.useCallback(() => {
        if (folder !== null) void exportFlow.run(folder);
    }, [exportFlow, folder]);

    const onApplyMigration = React.useCallback(() => {
        void migration.apply();
    }, [migration]);

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={refreshDoc} />
            <FolderSection folder={folder} onPick={pickFolder} onClear={clearFolder} />
            <ExportSection
                opts={exportFlow.opts}
                busy={exportFlow.busy}
                disabled={exportDisabled}
                last={exportFlow.last}
                polygonTemplate={templates.polygonTemplate}
                framesTemplate={templates.framesTemplate}
                polygonDefault={templates.defaults.polygon}
                framesDefault={templates.defaults.frames}
                pixelsPerUnit={ppu.pixelsPerUnit}
                pixelsPerUnitDefault={ppu.defaultValue}
                docHeight={doc?.height ?? null}
                onToggleOption={exportFlow.setOption}
                onPolygonTemplateChange={templates.setPolygonTemplate}
                onFramesTemplateChange={templates.setFramesTemplate}
                onResetTemplates={templates.reset}
                onPixelsPerUnitChange={ppu.setPixelsPerUnit}
                onExport={onExport}
            />
            <ReexportSection
                preview={preview.preview}
                activeLayerPath={activeLayerPath}
                folder={folder}
                opts={reexportOpts}
            />
            <ImportSection
                busy={importFlow.busy}
                last={importFlow.last}
                manifestErrors={importFlow.manifestErrors}
                onImport={importFlow.run}
            />
            <MigrationSection
                preview={migration.preview}
                busy={migration.busy}
                lastResult={migration.lastResult}
                onApply={onApplyMigration}
            />
        </div>
    );
};
