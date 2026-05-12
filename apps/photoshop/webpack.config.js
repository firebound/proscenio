// webpack config for the Proscenio UXP plugin (apps/photoshop/).
//
// Targets the UXP runtime (Photoshop CC 2021+). Native CommonJS, no
// ESM-only deps. Babel transpiles TS / TSX via `@babel/preset-typescript`;
// `tsc --noEmit` runs separately as the type gate (`pnpm run typecheck`).
//
// Externals (`uxp`, `photoshop`, `os`) are resolved by the UXP host at
// load time, not bundled. Without these declarations webpack would try
// to bundle the Photoshop API surface and fail.

const path = require("node:path");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
    entry: "./src/index.tsx",
    output: {
        path: path.resolve(__dirname, "dist"),
        filename: "index.js",
    },
    devtool: "eval-cheap-source-map",
    externals: {
        uxp: "commonjs2 uxp",
        photoshop: "commonjs2 photoshop",
        os: "commonjs2 os",
        // UXP scaffold imports `node:os`. Webpack 5 treats `node:` as an
        // unhandled URI scheme unless the external is declared with the
        // prefix; map it to the same commonjs2 require the host resolves.
        "node:os": "commonjs2 os",
    },
    resolve: {
        extensions: [".ts", ".tsx", ".js", ".jsx"],
    },
    module: {
        rules: [
            {
                test: /\.(ts|tsx|js|jsx)$/,
                exclude: /node_modules/,
                loader: "babel-loader",
                options: {
                    presets: ["@babel/preset-typescript"],
                    plugins: [
                        "@babel/transform-react-jsx",
                        "@babel/plugin-transform-object-rest-spread",
                        "@babel/plugin-syntax-class-properties",
                    ],
                },
            },
            {
                // Webpack 5 asset modules replace file-loader. Emits the PNG
                // alongside the bundle with a hashed filename and produces a
                // JS-import URL that resolves to that path at runtime.
                test: /\.png$/,
                exclude: /node_modules/,
                type: "asset/resource",
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"],
            },
        ],
    },
    plugins: [
        // CleanWebpackPlugin@4 ships a named export. Removes stale `dist/`
        // artefacts before each build so `uxp plugin load` does not pick
        // up the previous bundle.
        new CleanWebpackPlugin(),
        // CopyPlugin@14 changed the API: positional patterns argument moved
        // into the `patterns` field of the options object. `copyUnmodified`
        // was removed; v14 copies modified files only by default which is
        // the behaviour the plugin uses anyway.
        new CopyPlugin({
            patterns: [{ from: "plugin", to: "." }],
        }),
    ],
};
