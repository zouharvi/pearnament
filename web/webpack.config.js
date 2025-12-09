const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const TerserPlugin = require("terser-webpack-plugin");

// Change module.exports to an arrow function
module.exports = (env, argv) => {
  return {
    entry: {
      pointwise: './src/pointwise.ts',
      listwise: './src/listwise.ts',
      dashboard: './src/dashboard.ts',
    },
    output: {
      filename: '[name].bundle.js',
      path: path.resolve(__dirname, '../server/static'),
      clean: true,
    },
    optimization: {
      minimize: true,
      minimizer: [
        new TerserPlugin({
          extractComments: false,
          terserOptions: {
            format: {
              comments: false,
            },
          },
        }),
      ],
    },

    module: {
      rules: [
        {
          test: /\.ts$/,
          use: 'ts-loader',
          exclude: /node_modules/,
        },
      ],
    },
    resolve: {
      extensions: ['.ts', '.js'],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html',
        filename: 'index.html',
        chunks: [],
      }),
      new HtmlWebpackPlugin({
        template: './src/pointwise.html',
        filename: 'pointwise.html',
        chunks: ['pointwise'],
      }),
      new HtmlWebpackPlugin({
        template: './src/listwise.html',
        filename: 'listwise.html',
        chunks: ['listwise'],
      }),
      new HtmlWebpackPlugin({
        template: './src/dashboard.html',
        filename: 'dashboard.html',
        chunks: ['dashboard'],
      }),
      new CopyWebpackPlugin({
        patterns: [
          { from: 'src/favicon.svg', to: '.' },
          { from: 'src/style.css', to: '.' },
        ],
      }),
    ],
    devServer: {
      static: '../server/static',
      port: 8000,
      open: true,
    },
    // Set the mode based on the CLI argument
    mode: argv.mode || 'development',

    devtool: argv.mode === 'production' ? false : 'source-map',
  };
};