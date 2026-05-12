// Spectrum web component JSX intrinsics. Adobe's Spectrum components
// render natively under UXP and inherit the Photoshop theme; they are
// not in React's JSX intrinsic table, so each panel that uses them
// would otherwise have to redeclare the JSX namespace.
//
// The prop surface is intentionally minimal - we widen as the panels
// touch new attributes. Forking the upstream Spectrum typings package
// is not worth the build complexity for the small surface we use.

import "react";

declare global {
    namespace JSX {
        interface IntrinsicElements {
            "sp-heading": SpectrumElementProps;
            "sp-body": SpectrumElementProps;
            "sp-checkbox": SpectrumCheckboxProps;
            "sp-action-button": SpectrumActionButtonProps;
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
}
