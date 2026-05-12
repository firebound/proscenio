import React from "react";
import type { UxpFolder } from "uxp";

interface Props {
    folder: UxpFolder | null;
    onPick: () => void;
    onClear: () => void;
}

export const FolderSection: React.FC<Props> = ({ folder, onPick, onClear }) => (
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
