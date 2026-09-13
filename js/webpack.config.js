'use strict'

const path = require('path')
const autoprefixer = require('autoprefixer')
const webpack = require('webpack')
const miniCssExtractPlugin = require('mini-css-extract-plugin')

module.exports = {
    mode: 'production',
    entry: {
        libs: './src/js/libs.js',
        plotly: './src/js/plotly.js',
        leaflet: './src/js/leaflet.js',
    },
    output: {
        filename: '[name].js',
        chunkFilename: '[id].js',
        path: path.resolve(__dirname, '../sporttracker/static/js/libs'),
        clean: {
            keep: /(^fontawesome|^swaggerui)/,
        },
    },
    optimization: {
        splitChunks: false,
    },
    plugins: [
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
        }),
        new miniCssExtractPlugin({
            filename: '[name].css',
        }),
    ],
    resolve: {
        fallback: {
            "url": require.resolve("url/"),
            "assert": require.resolve("assert/"),
            "stream": require.resolve("stream-browserify"),
            "buffer": require.resolve("buffer/")
        }
    },
    module: {
        rules: [
            {
                test: /\.(scss)$/,
                use: [
                    {
                        // Extracts CSS for each JS file that includes CSS
                        loader: miniCssExtractPlugin.loader
                    },
                    {
                        // Interprets `@import` and `url()` like `import/require()` and will resolve them
                        loader: 'css-loader'
                    },
                    {
                        // Loader for webpack to process CSS with PostCSS
                        loader: 'postcss-loader',
                        options: {
                            postcssOptions: {
                                plugins: [
                                    autoprefixer
                                ]
                            }
                        }
                    },
                    {
                        // Loads a SASS/SCSS file and compiles it to CSS
                        loader: 'sass-loader'
                    }
                ]
            },
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader'
                ]
            },
            {
                test: /\.(png|svg|jpg|gif)$/,
                use: {
                    loader: "file-loader",
                },
            },
        ]
    }
}