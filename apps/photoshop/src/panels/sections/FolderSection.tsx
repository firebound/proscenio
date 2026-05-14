import React from "react";
import type { UxpFolder } from "uxp";

import { Accordion } from "../common/Accordion";

interface Props {
    folder: UxpFolder | null;
    onPick: () => void;
    onClear: () => void;
}

export const FolderSection: React.FC<Props> = ({ folder, onPick, onClear }) => (
    <Accordion
        title="Output folder"
        hint="Where the export writes the manifest + PNGs. The path persists across plugin reloads."
    >
        {folder === null ? (
            <div className="placeholder-card">No folder picked.</div>
        ) : (
            <div className="path-display" title={folder.nativePath}>
                {folder.nativePath}
            </div>
        )}
        <div className="row">
            <sp-action-button onClick={onPick}>
                {folder === null ? "Pick folder" : "Change folder"}
            </sp-action-button>
            {folder !== null && <sp-action-button onClick={onClear}>Forget</sp-action-button>}
        </div>
    </Accordion>
);
