// Spectrum web component JSX intrinsics. Adobe's Spectrum components
// render natively under UXP and inherit the Photoshop theme; they are
// not in React's JSX intrinsic table, so each panel that uses them
// would otherwise have to redeclare the JSX namespace.
//
// Optional props explicitly include `| undefined` so the panels can
// pass through state-derived values that may be undefined under
// `exactOptionalPropertyTypes: true`. React DOM treats `prop={undefined}`
// as absent at runtime, matching Spectrum's actual behaviour - this
// widening is honest, not a workaround.
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
            "sp-textfield": SpectrumTextfieldProps;
        }
    }

    interface SpectrumElementProps extends React.HTMLAttributes<HTMLElement>, React.Attributes {
        size?: "XS" | "S" | "M" | "L" | "XL" | undefined;
    }

    interface SpectrumCheckboxProps extends SpectrumElementProps {
        checked?: boolean | undefined;
        disabled?: boolean | undefined;
        onChange?: ((e: React.SyntheticEvent) => void) | undefined;
    }

    interface SpectrumActionButtonProps extends SpectrumElementProps {
        disabled?: boolean | undefined;
        quiet?: "true" | undefined;
        onClick?: ((e: React.SyntheticEvent) => void) | undefined;
    }

    interface SpectrumTextfieldProps extends SpectrumElementProps {
        value?: string | undefined;
        placeholder?: string | undefined;
        disabled?: boolean | undefined;
        onInput?: ((e: React.SyntheticEvent) => void) | undefined;
        onChange?: ((e: React.SyntheticEvent) => void) | undefined;
    }
}
