// @ts-nocheck - Adobe React Starter scaffold; will be deleted/replaced in Wave 10.2+ when Proscenio panels land.
import React from "react";

import { Hello } from "../components/Hello";
import { PlayIcon } from "../components/Icons";

export const MoreDemos = () => {
    return (
        <>
            <Hello message="there"/>
            <sp-button variant="primary">
                <span slot="icon"><PlayIcon /></span>
            </sp-button>
        </>
    );
    }
