const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const TerserPlugin = require("terser-webpack-plugin");

module.exports = {
  entry: {
    pointwise: './src/pointwise.ts',
    dashboard: './src/dashboard.ts',
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, '../static'),
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
      template: './src/dashboard.html',
      filename: 'dashboard.html',
      chunks: ['dashboard'],
    }),
    new CopyWebpackPlugin({
      patterns: [
        { from: 'src/assets', to: 'assets' },
      ],
    }),
  ],
  devServer: {
    static: '../static',
    port: 8000,
    open: true,
  },
  mode: 'development',
  devtool: 'source-map',
};