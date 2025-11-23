const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: {
    ESA: './src/ESA.ts',
    dashboard: './src/dashboard.ts',
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, 'dist'),
    clean: true,
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
      template: './src/ESA.html',
      filename: 'ESA.html',
      chunks: ['ESA'],
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
    static: './dist',
    port: 8080,
    open: true,
  },
  mode: 'development',
  devtool: 'source-map',
};