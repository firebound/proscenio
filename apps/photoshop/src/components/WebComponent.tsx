// @ts-nocheck - Adobe React Starter scaffold; will be deleted/replaced in Wave 10.2+ when Proscenio panels land.
import React, { useEffect, useRef } from "react";

export const WebComponent = ({ children, ...rest }) => { // NOSONAR S6774: scaffold; PropTypes will arrive with TypeScript port (SPEC 010)
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
