import React from "react";

import type { ExportFlowResult } from "../../controllers/export-flow";
import type { ExportOptions } from "../../domain/planner";

interface Props {
    opts: ExportOptions;
    busy: boolean;
    disabled: boolean;
    last: ExportFlowResult | null;
    polygonTemplate: string;
    framesTemplate: string;
    polygonDefault: string;
    framesDefault: string;
    pixelsPerUnit: number;
    pixelsPerUnitDefault: number;
    docHeight: number | null;
    onToggleOption: <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => void;
    onPolygonTemplateChange: (value: string) => void;
    onFramesTemplateChange: (value: string) => void;
    onResetTemplates: () => void;
    onPixelsPerUnitChange: (value: number) => void;
    onExport: () => void;
}

export const ExportSection: React.FC<Props> = ({
    opts,
    busy,
    disabled,
    last,
    polygonTemplate,
    framesTemplate,
    polygonDefault,
    framesDefault,
    pixelsPerUnit,
    pixelsPerUnitDefault,
    docHeight,
    onToggleOption,
    onPolygonTemplateChange,
    onFramesTemplateChange,
    onResetTemplates,
    onPixelsPerUnitChange,
    onExport,
}) => {
    const onSkipHidden = React.useCallback(
        (e: React.SyntheticEvent) => {
            onToggleOption("skipHidden", (e.target as HTMLInputElement).checked);
        },
        [onToggleOption],
    );
    const onPolygonInput = React.useCallback(
        (e: React.SyntheticEvent) => {
            onPolygonTemplateChange((e.target as HTMLInputElement).value);
        },
        [onPolygonTemplateChange],
    );
    const onFramesInput = React.useCallback(
        (e: React.SyntheticEvent) => {
            onFramesTemplateChange((e.target as HTMLInputElement).value);
        },
        [onFramesTemplateChange],
    );
    const onPpuInput = React.useCallback(
        (e: React.SyntheticEvent) => {
            const raw = (e.target as HTMLInputElement).value;
            const parsed = Number.parseFloat(raw);
            if (Number.isFinite(parsed) && parsed > 0) onPixelsPerUnitChange(parsed);
        },
        [onPixelsPerUnitChange],
    );

    const templatesAreDefault = polygonTemplate === polygonDefault && framesTemplate === framesDefault;
    const heightInUnits = docHeight !== null && pixelsPerUnit > 0
        ? docHeight / pixelsPerUnit
        : null;
    const ppuIsDefault = pixelsPerUnit === pixelsPerUnitDefault;

    return (
        <>
            <section className="section">
                <sp-heading size="XS">Export options</sp-heading>
                <sp-checkbox checked={opts.skipHidden ? true : undefined} onChange={onSkipHidden}>
                    Skip hidden layers
                </sp-checkbox>
                <sp-body size="XS" className="muted">
                    Use the [ignore] tag in a layer or group name to exclude it from the export.
                </sp-body>
            </section>
            <section className="section">
                <sp-heading size="XS">Pixels per unit</sp-heading>
                <sp-body size="XS" className="muted">
                    Conversion factor for Blender / Godot. Higher PPU = smaller world-space objects. Default {pixelsPerUnitDefault}.
                </sp-body>
                <sp-textfield
                    value={String(pixelsPerUnit)}
                    placeholder={String(pixelsPerUnitDefault)}
                    onInput={onPpuInput}
                ></sp-textfield>
                {heightInUnits !== null && (
                    <sp-body size="XS" className="muted">
                        Canvas height {docHeight}px = {heightInUnits.toFixed(2)} units.
                    </sp-body>
                )}
                <sp-action-button
                    onClick={() => onPixelsPerUnitChange(pixelsPerUnitDefault)}
                    disabled={ppuIsDefault ? true : undefined}
                >
                    Reset to {pixelsPerUnitDefault}
                </sp-action-button>
            </section>
            <section className="section">
                <sp-heading size="XS">Filename templates</sp-heading>
                <sp-body size="XS" className="muted">
                    Tokens: {"{name}"} and {"{kind}"} for polygons; {"{name}"} and {"{index}"} for frames. The images/ prefix and any [folder:...] subfolder are added automatically.
                </sp-body>
                <sp-body size="XS">Polygon / mesh</sp-body>
                <sp-textfield
                    value={polygonTemplate}
                    placeholder={polygonDefault}
                    onInput={onPolygonInput}
                ></sp-textfield>
                <sp-body size="XS">Sprite frame</sp-body>
                <sp-textfield
                    value={framesTemplate}
                    placeholder={framesDefault}
                    onInput={onFramesInput}
                ></sp-textfield>
                <sp-action-button
                    onClick={onResetTemplates}
                    disabled={templatesAreDefault ? true : undefined}
                >
                    Reset to defaults
                </sp-action-button>
            </section>
            <sp-action-button onClick={onExport} disabled={disabled ? true : undefined}>
                {busy ? "Exporting..." : "Export manifest + PNGs"}
            </sp-action-button>
            {last !== null && <ExportResultView result={last} />}
        </>
    );
};

const ExportResultView: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Wrote {result.entryCount} entry(ies) to {result.manifestFile}
                </sp-body>
                {(result.pngResults ?? [])
                    .filter((r) => !r.ok)
                    .map((r) => (
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
