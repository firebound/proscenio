// Reusable primitives for the Tags panel rows. UXP's Adobe Clean font
// does not render Unicode geometric shapes, so we use ASCII glyphs.
// `<button>` elements drop their text content in UXP's mini-DOM, so
// every interactive surface in the row is a `<span role="button">`
// with keyboard handlers attached.

import React from "react";

export const GLYPH_OPEN = "v";
export const GLYPH_CLOSED = ">";
export const GLYPH_IGNORE = "X";
export const GLYPH_MERGE = "M";
export const GLYPH_EXPAND = "+";
export const GLYPH_COLLAPSE = "-";

interface ClickSpanProps {
    className: string;
    title: string;
    disabled: boolean;
    onClick: () => void;
    children: React.ReactNode;
}

export const ClickSpan: React.FC<ClickSpanProps> = ({
    className,
    title,
    disabled,
    onClick,
    children,
}) => {
    const handleClick = React.useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            if (!disabled) onClick();
        },
        [disabled, onClick],
    );
    const handleKey = React.useCallback(
        (e: React.KeyboardEvent) => {
            if (disabled) return;
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                e.stopPropagation();
                onClick();
            }
        },
        [disabled, onClick],
    );
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    return (
        <span
            className={className}
            role="button"
            tabIndex={disabled ? -1 : 0}
            title={title}
            onClick={handleClick}
            onKeyDown={handleKey}
        >
            {children}
        </span>
    );
};

interface GlyphToggleProps {
    glyph: string;
    title: string;
    active: boolean;
    disabled: boolean;
    onClick: () => void;
}

export const GlyphToggle: React.FC<GlyphToggleProps> = ({
    glyph,
    title,
    active,
    disabled,
    onClick,
}) => {
    const className = `tag-toggle${active ? " active" : ""}${disabled ? " disabled" : ""}`;
    return (
        <ClickSpan className={className} title={title} disabled={disabled} onClick={onClick}>
            {glyph}
        </ClickSpan>
    );
};
