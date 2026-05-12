// UXP panel host adapter. Bridges between Adobe's `entrypoints.setup`
// contract (`create`, `show`, `hide`, `destroy`, `invokeMenu`) and a
// React function component.
//
// Replaces the Adobe React Starter scaffold's untyped JS version
// (which used Symbol-keyed private fields and `@ts-nocheck`) with a
// minimal typed equivalent. The only behaviour we use is: render the
// component into a div on `create`, attach / detach on `show` / `hide`,
// dispatch menu invocations.

import React from "react";
import ReactDOM from "react-dom";

export interface PanelMenuItem {
    id: string;
    label: string;
    enabled?: boolean;
    checked?: boolean;
    oninvoke: () => void;
}

export interface PanelControllerOptions {
    id: string;
    menuItems?: PanelMenuItem[];
}

export interface PanelMenuDescriptor {
    id: string;
    label: string;
    enabled: boolean;
    checked: boolean;
}

export class PanelController {
    public readonly id: string;
    public readonly menuItems: PanelMenuDescriptor[];

    private root: HTMLDivElement | null = null;
    private attachment: HTMLElement | null = null;
    private readonly Component: React.FC;
    private readonly menuHandlers: Map<string, () => void>;

    constructor(Component: React.FC, opts: PanelControllerOptions) {
        this.id = opts.id;
        this.Component = Component;
        const items = opts.menuItems ?? [];
        this.menuItems = items.map((item) => ({
            id: item.id,
            label: item.label,
            enabled: item.enabled ?? true,
            checked: item.checked ?? false,
        }));
        this.menuHandlers = new Map(items.map((item) => [item.id, item.oninvoke]));
        this.create = this.create.bind(this);
        this.show = this.show.bind(this);
        this.hide = this.hide.bind(this);
        this.destroy = this.destroy.bind(this);
        this.invokeMenu = this.invokeMenu.bind(this);
    }

    public create(): HTMLDivElement {
        this.root = document.createElement("div");
        this.root.style.height = "100vh";
        this.root.style.overflow = "auto";
        const Component = this.Component;
        ReactDOM.render(<Component />, this.root);
        return this.root;
    }

    public show(event: HTMLElement): void {
        if (this.root === null) this.create();
        this.attachment = event;
        if (this.root !== null) event.appendChild(this.root);
    }

    public hide(): void {
        if (this.attachment !== null && this.root !== null) {
            this.root.remove();
            this.attachment = null;
        }
    }

    public destroy(): void {
        // No lifecycle teardown beyond the implicit unmount when the
        // host destroys the panel; React state goes with the DOM tree.
    }

    public invokeMenu(id: string): void {
        const handler = this.menuHandlers.get(id);
        if (handler !== undefined) handler();
    }
}
