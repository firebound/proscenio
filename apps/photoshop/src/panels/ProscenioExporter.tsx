// Proscenio main panel. Hosts both directions of the manifest <-> PSD
// roundtrip:
//
// - Export: active PSD -> manifest JSON + per-layer PNGs (the SPEC 010
//   primary path).
// - Import: manifest JSON -> reconstructed PSD with placed layers
//   (the SPEC 010 roundtrip mirror, formerly proscenio_import.jsx).
//
// Spectrum web components render natively in UXP and inherit the
// Photoshop theme. They are not in React's JSX intrinsic table, so
// they are declared as minimal interfaces at the bottom.

import React from "react";
import { app } from "photoshop";
import type { UxpFolder } from "uxp";

import { runExport, type ExportFlowResult } from "../controllers/export-flow";
import type { ExportOptions } from "../controllers/exporter";
import { runImport, type ImportFlowResult } from "../controllers/import-flow";
import { clearRememberedFolder, pickFolder, restoreFolder } from "../io/folder-storage";
import { readManifestFromPicker, type ReadManifestResult } from "../io/manifest-reader";

const DEFAULT_OPTS: ExportOptions = {
    skipHidden: true,
    skipUnderscorePrefix: true,
};

interface DocSnapshot {
    name: string;
    width: number;
    height: number;
}

export const ProscenioExporter: React.FC = () => {
    const [opts, setOpts] = React.useState<ExportOptions>(DEFAULT_OPTS);
    const [folder, setFolder] = React.useState<UxpFolder | null>(null);
    const [doc, setDoc] = React.useState<DocSnapshot | null>(null);
    const [busyExport, setBusyExport] = React.useState(false);
    const [busyImport, setBusyImport] = React.useState(false);
    const [lastExport, setLastExport] = React.useState<ExportFlowResult | null>(null);
    const [lastImport, setLastImport] = React.useState<ImportFlowResult | null>(null);
    const [importError, setImportError] = React.useState<string[] | null>(null);

    React.useEffect(() => {
        let cancelled = false;
        void restoreFolder().then((restored) => {
            if (!cancelled) setFolder(restored);
        });
        readDocSnapshot().then((snap) => {
            if (!cancelled) setDoc(snap);
        });
        return () => {
            cancelled = true;
        };
    }, []);

    const onPickFolder = React.useCallback(async () => {
        const picked = await pickFolder();
        if (picked !== null) setFolder(picked);
    }, []);

    const onClearFolder = React.useCallback(() => {
        clearRememberedFolder();
        setFolder(null);
    }, []);

    const onRefreshDoc = React.useCallback(async () => {
        setDoc(await readDocSnapshot());
    }, []);

    const onExport = React.useCallback(async () => {
        if (folder === null) return;
        setBusyExport(true);
        try {
            const result = await runExport(opts, folder);
            setLastExport(result);
        } finally {
            setBusyExport(false);
        }
    }, [opts, folder]);

    const onImport = React.useCallback(async () => {
        setImportError(null);
        const picked: ReadManifestResult = await readManifestFromPicker();
        if (picked.kind === "cancelled") return;
        if (picked.kind === "invalid") {
            setImportError(picked.errors);
            return;
        }
        setBusyImport(true);
        try {
            const result = await runImport(picked.picked.manifest, picked.picked.folder);
            setLastImport(result);
        } finally {
            setBusyImport(false);
        }
    }, []);

    const onToggleHidden = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipHidden: checked }));
    }, []);

    const onToggleUnderscore = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipUnderscorePrefix: checked }));
    }, []);

    const exportDisabled = busyExport || folder === null || doc === null;
    const importDisabled = busyImport;

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={onRefreshDoc} />
            <FolderSection folder={folder} onPick={onPickFolder} onClear={onClearFolder} />
            <section className="section">
                <sp-heading size="XS">Export options</sp-heading>
                <sp-checkbox checked={opts.skipHidden ? true : undefined} onChange={onToggleHidden}>
                    Skip hidden layers
                </sp-checkbox>
                <sp-checkbox
                    checked={opts.skipUnderscorePrefix ? true : undefined}
                    onChange={onToggleUnderscore}
                >
                    Skip layers starting with _
                </sp-checkbox>
            </section>
            <sp-action-button
                onClick={onExport}
                disabled={exportDisabled ? true : undefined}
            >
                {busyExport ? "Exporting..." : "Export manifest + PNGs"}
            </sp-action-button>
            {lastExport !== null && <ExportResultView result={lastExport} />}

            <section className="section">
                <sp-heading size="XS">Import (manifest to PSD)</sp-heading>
                <sp-body size="XS" className="muted">
                    Pick a Proscenio manifest JSON. The plugin recreates the
                    PSD with placed layers / sprite_frame groups; saved under
                    the manifest folder's photoshop/ subfolder.
                </sp-body>
                <sp-action-button onClick={onImport} disabled={importDisabled ? true : undefined}>
                    {busyImport ? "Importing..." : "Import manifest as PSD"}
                </sp-action-button>
            </section>
            {importError !== null && <ManifestErrors errors={importError} />}
            {lastImport !== null && <ImportResultView result={lastImport} />}
        </div>
    );
};

const DocSection: React.FC<{ doc: DocSnapshot | null; onRefresh: () => void }> = ({
    doc,
    onRefresh,
}) => (
    <section className="section">
        <sp-heading size="XS">Active document</sp-heading>
        {doc === null ? (
            <sp-body size="XS" className="muted">
                No document open in Photoshop.
            </sp-body>
        ) : (
            <sp-body size="XS">
                {doc.name} - {doc.width} x {doc.height} px
            </sp-body>
        )}
        <sp-action-button quiet="true" onClick={onRefresh}>
            Refresh
        </sp-action-button>
    </section>
);

const FolderSection: React.FC<{
    folder: UxpFolder | null;
    onPick: () => void;
    onClear: () => void;
}> = ({ folder, onPick, onClear }) => (
    <section className="section">
        <sp-heading size="XS">Output folder</sp-heading>
        {folder === null ? (
            <sp-body size="XS" className="muted">
                Pick a folder. Path is remembered across plugin reloads.
            </sp-body>
        ) : (
            <sp-body size="XS" className="folder-path">
                {folder.nativePath}
            </sp-body>
        )}
        <div className="row">
            <sp-action-button onClick={onPick}>
                {folder === null ? "Pick folder" : "Change folder"}
            </sp-action-button>
            {folder !== null && (
                <sp-action-button quiet="true" onClick={onClear}>
                    Forget
                </sp-action-button>
            )}
        </div>
    </section>
);

const ExportResultView: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Wrote {result.entryCount} entry(ies) to {result.manifestFile}
                </sp-body>
                {(result.pngResults ?? []).filter((r) => !r.ok).map((r) => (
                    <sp-body size="XS" className="result-row warn" key={r.outputPath}>
                        {r.outputPath}: {r.skippedReason ?? "failed"}
                    </sp-body>
                ))}
            </div>
        );
    }
    return (
        <div className="result error">
            <sp-body size="XS">Export {result.kind}.</sp-body>
            {(result.errors ?? []).map((err) => (
                <sp-body size="XS" key={err} className="result-row">
                    {err}
                </sp-body>
            ))}
        </div>
    );
};

const ImportResultView: React.FC<{ result: ImportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Stamped {result.stamped} entry(ies)
                    {result.skipped !== undefined && result.skipped > 0
                        ? ` (${result.skipped} skipped)`
                        : ""}
                    .
                </sp-body>
                {result.psdPath !== undefined && (
                    <sp-body size="XS" className="folder-path">
                        {result.psdPath}
                    </sp-body>
                )}
                {(result.warnings ?? []).map((w) => (
                    <sp-body size="XS" className="result-row warn" key={w}>
                        {w}
                    </sp-body>
                ))}
            </div>
        );
    }
    return (
        <div className="result error">
            <sp-body size="XS">Import failed.</sp-body>
            {(result.errors ?? []).map((err) => (
                <sp-body size="XS" key={err} className="result-row">
                    {err}
                </sp-body>
            ))}
        </div>
    );
};

const ManifestErrors: React.FC<{ errors: string[] }> = ({ errors }) => (
    <div className="result error">
        <sp-body size="XS">Manifest invalid.</sp-body>
        {errors.map((err) => (
            <sp-body size="XS" key={err} className="result-row">
                {err}
            </sp-body>
        ))}
    </div>
);

async function readDocSnapshot(): Promise<DocSnapshot | null> {
    const d = app.activeDocument;
    if (d === null) return null;
    return { name: d.name, width: d.width, height: d.height };
}

declare global {
    namespace JSX {
        interface IntrinsicElements {
            "sp-heading": SpectrumElementProps;
            "sp-body": SpectrumElementProps;
            "sp-checkbox": SpectrumCheckboxProps;
            "sp-action-button": SpectrumActionButtonProps;
        }
    }
}

interface SpectrumElementProps extends React.HTMLAttributes<HTMLElement>, React.Attributes {
    size?: "XS" | "S" | "M" | "L" | "XL";
}

interface SpectrumCheckboxProps extends SpectrumElementProps {
    checked?: boolean;
    onChange?: (e: React.SyntheticEvent) => void;
}

interface SpectrumActionButtonProps extends SpectrumElementProps {
    disabled?: boolean;
    quiet?: "true";
    onClick?: (e: React.SyntheticEvent) => void;
}
