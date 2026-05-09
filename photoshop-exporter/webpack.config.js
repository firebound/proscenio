const path = require("node:path");
const CleanWebpackPlugin = require("clean-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
    entry: './src/index.jsx',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'index.js',
        //libraryTarget: "commonjs2"
    },
    devtool: 'eval-cheap-source-map', // won't work on XD due to lack of eval
    externals: {
        uxp: 'commonjs2 uxp',
        photoshop: 'commonjs2 photoshop',
        os: 'commonjs2 os'
    },
    resolve: {
        extensions: [".ts", ".tsx", ".js", ".jsx"]
    },
    module: {
        rules: [
            {
                test: /\.(ts|tsx|js|jsx)$/,
                exclude: /node_modules/,
                loader: "babel-loader",
                options: {
                    presets: [
                        "@babel/preset-typescript"
                    ],
                    plugins: [
                        "@babel/transform-react-jsx",
                        "@babel/plugin-transform-object-rest-spread",
                        "@babel/plugin-syntax-class-properties",
                    ]
                }
            },
            {
                test: /\.png$/,
                exclude: /node_modules/,
                loader: 'file-loader'
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"]
            }
        ]
    },
    plugins: [
        //new CleanWebpackPlugin(),
        new CopyPlugin(['plugin'], {
            copyUnmodified: true
        })
    ]
};
