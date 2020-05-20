const reactLint = require('@mozilla-frontend-infra/react-lint')
const react = require('@neutrinojs/react');
const jest = require('@neutrinojs/jest');

const DEFAULT_HOST = 'localhost';
const DEFAULT_PORT = 8010;
const host = process.env.HOST || DEFAULT_HOST;
const port = process.env.PORT || DEFAULT_PORT;
const SHIPIT_PUBLIC_API_URL = process.env.SHIPIT_PUBLIC_API_URL;
const SHIPIT_API_URL = process.env.SHIPIT_API_URL;
const FRONTEND_TASKCLUSTER_ROOT_URL = process.env.FRONTEND_TASKCLUSTER_ROOT_URL;
const connectSrc = [
  'https://hg.mozilla.org',
  'https://auth.mozilla.auth0.com',
  SHIPIT_API_URL,
  SHIPIT_PUBLIC_API_URL,
  FRONTEND_TASKCLUSTER_ROOT_URL,
  "'self'",
].join(' ');
module.exports = {
  options: {
    root: __dirname,
  },
  use: [
    reactLint({
      rules: {
        'react/jsx-props-no-spreading': 'off',
        'react-hooks/exhaustive-deps': 'off',
      }
    }),
    react({
      devServer: {
        host,
        port,
        https: true,
        historyApiFallback: {
          disableDotRule: true,
        },
        headers: {
          'Content-Security-Policy':
            `connect-src ${connectSrc}; ` +
            "default-src https://auth.mozilla.auth0.com 'none'; " +
            "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.auth0.com; " +
            "img-src 'self' https://*.gravatar.com https://i1.wp.com data:; " +
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
            "font-src https://fonts.gstatic.com; " +
            "frame-ancestors 'none'; " +
            "base-uri 'none'; " +
            "form-action 'none'",
          'X-Frame-Options': 'SAMEORIGIN',
          'X-Content-Type-Options': 'nosniff',
          'X-XSS-Protection': '1; mode=block',
          'Referrer-Policy': 'no-referrer',
          'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; always;',
        },
      },
      html: {
        favicon: `${__dirname}/src/images/shipit.png`,
        template: 'src/index.html',
      },
      env: {
        HOST: host,
        PORT: port,
        SHIPIT_API_URL,
        SHIPIT_PUBLIC_API_URL,
        RELEASE_CHANNEL: process.env.RELEASE_CHANNEL,
      },
    }),
    (neutrino) => {
      neutrino.config.resolve.alias
        .set('react-dom', '@hot-loader/react-dom');

      neutrino.config.output.set('globalObject', 'this');
      neutrino.config.module
        .rule('worker')
          .test(/\.worker\.js$/)
          .use('worker')
            .loader(require.resolve('worker-loader'));
    },
    jest()
  ]
};
