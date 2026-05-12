// Proscenio exporter panel. Full UXP equivalent of the JSX dialog:
// shows the active document info, the cached output folder (persisted
// across plugin reloads via a UXP persistent token), the skipHidden /
// skipUnderscorePrefix toggles, an Export button and the result of
// the last run.
//
// Spectrum web components (`<sp-checkbox>`, `<sp-action-button>`,
// `<sp-body>`, `<sp-heading>`) render natively in UXP and inherit the
// Photoshop theme. They are not in React's JSX intrinsic table, so
// they are declared as minimal interfaces below.

import React from "react";
import { app } from "photoshop";
import type { UxpFolder } from "uxp";

import { runExport, type ExportFlowResult } from "../controllers/export-flow";
import type { ExportOptions } from "../controllers/exporter";
import { clearRememberedFolder, pickFolder, restoreFolder } from "../io/folder-storage";

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
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<ExportFlowResult | null>(null);

    // Restore the persisted folder on first mount. Refresh the doc
    // snapshot at the same time so the header is populated when the
    // panel pops open against an already-open document.
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
        setBusy(true);
        try {
            const result = await runExport(opts, folder);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, [opts, folder]);

    const onToggleHidden = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipHidden: checked }));
    }, []);

    const onToggleUnderscore = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipUnderscorePrefix: checked }));
    }, []);

    const exportDisabled = busy || folder === null || doc === null;

    return (
        <div className="proscenio-panel">
            <DocSection doc={doc} onRefresh={onRefreshDoc} />
            <FolderSection folder={folder} onPick={onPickFolder} onClear={onClearFolder} />
            <section className="section">
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
                {busy ? "Exporting..." : "Export manifest + PNGs"}
            </sp-action-button>
            {last !== null && <ExportResult result={last} />}
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

const ExportResult: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
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
