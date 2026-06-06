// Compact key/value row used across the Proscenio panels. Mirrors the
// `Selected entry` pattern in Tags: small uppercase label on the left,
// value (string or rich content) on the right.

import React from "react";

interface Props {
    label: string;
    /** Plain text value. For richer content (inputs, buttons) pass
     *  `children` instead. */
    value?: React.ReactNode;
    mono?: boolean;
    hint?: string;
    children?: React.ReactNode;
}

export const KeyValueRow: React.FC<Props> = ({ label, value, mono, hint, children }) => (
    <div className="kv-row" title={hint}>
        <span className="kv-label">{label}</span>
        <span className={mono === true ? "kv-value mono" : "kv-value"}>
            {children ?? value}
        </span>
    </div>
);
