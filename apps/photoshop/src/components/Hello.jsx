import React from "react";

export const Hello = ({ message }) => { // NOSONAR S6774: scaffold; PropTypes will arrive with TypeScript port (SPEC 010)
    return (
        <sp-body>Hello, {message || "world"} </sp-body>
    );
}
