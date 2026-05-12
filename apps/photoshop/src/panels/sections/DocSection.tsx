import React from "react";

import type { DocSnapshot } from "../../hooks/useDocSnapshot";

interface Props {
    doc: DocSnapshot | null;
    onRefresh: () => void;
}

export const DocSection: React.FC<Props> = ({ doc, onRefresh }) => (
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
