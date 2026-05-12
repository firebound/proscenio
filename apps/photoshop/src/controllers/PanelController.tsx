// @ts-nocheck - Adobe React Starter scaffold; will be deleted/replaced in Wave 10.2+ when Proscenio panels land.
import ReactDOM from "react-dom";

const _id = Symbol("_id");
const _root = Symbol("_root");
const _attachment = Symbol("_attachment");
const _Component = Symbol("_Component");
const _menuItems = Symbol("_menuItems");

export class PanelController {

    constructor(Component, { id, menuItems } = {}) {
        this[_root] = null;
        this[_attachment] = null;
        this[_Component] = Component;
        this[_id] = id;
        this[_menuItems] = menuItems || [];
        this.menuItems = this[_menuItems].map(menuItem => ({
            id: menuItem.id,
            label: menuItem.label,
            enabled: menuItem.enabled || true,
            checked: menuItem.checked || false
        }));

        [ "create", "show", "hide", "destroy", "invokeMenu" ].forEach(fn => this[fn] = this[fn].bind(this));
    }

    create() {
        this[_root] = document.createElement("div");
        this[_root].style.height = "100vh";
        this[_root].style.overflow = "auto";
        this[_root].style.padding = "8px";

        ReactDOM.render(this[_Component]({panel: this}), this[_root]);

        return this[_root];
    }

    show(event)  {
        if (!this[_root]) this.create();
        this[_attachment] = event;
        this[_attachment].appendChild(this[_root]);
    }

    hide() {
        if (this[_attachment] && this[_root]) {
            this[_root].remove();
            this[_attachment] = null;
        }
    }

    destroy() {
        // Adobe React UXP starter scaffold leaves this empty; lifecycle teardown will be added during the SPEC 010 TypeScript port if needed.
    }

    invokeMenu(id) {
        const menuItem = this[_menuItems].find(c => c.id === id);
        if (menuItem) {
            const handler = menuItem.oninvoke;
            if (handler) {
                handler();
            }
        }
    }
}
