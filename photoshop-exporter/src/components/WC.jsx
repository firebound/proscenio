import React, { useEffect, useRef } from "react";

export const WC = ({ children, ...rest }) => { // NOSONAR S6774,S6770: scaffold; PropTypes + naming will arrive with TypeScript port (SPEC 010)
    const elRef = useRef(null);

    const handleEvent = (evt) => {
        const propName = `on${evt.type[0].toUpperCase()}${evt.type.substring(1)}`;
        if (rest[propName]) {
            rest[propName].call(evt.target, evt);
        }
    }

    useEffect(() => {
        const el = elRef.current;
        const eventProps = Object.entries(rest).filter(([k]) => k.startsWith("on"));
        eventProps.forEach(([k]) => el.addEventListener(k.substring(2).toLowerCase(), handleEvent));

        return () => {
            const elCleanup = elRef.current;
            const eventPropsCleanup = Object.entries(rest).filter(([k]) => k.startsWith("on"));
            eventPropsCleanup.forEach(([k]) => elCleanup.removeEventListener(k.substring(2).toLowerCase(), handleEvent));
        }
    }, []);

    return <div ref={elRef} {...rest}>{children}</div>
}
