module.exports = {
  TREEHERDER_URL: 'https://treeherder.mozilla.org',
  AUTH0: {
    domain: 'auth.mozilla.auth0.com',
    clientID: 'FK1mJkHhwjulTYBGklxn8W4Fhd1pgT4t',
    redirectUri: new URL('/login', window.location).href,
    scope: 'full-user-credentials openid profile email',
  },
  PRODUCTS: [
    {
      product: 'firefox',
      prettyName: 'Firefox Desktop',
      appName: 'browser',
      branches: [
        {
          prettyName: 'Maple Beta',
          project: 'maple',
          branch: 'projects/maple',
          repo: 'https://hg.mozilla.org/projects/maple',
          enableReleaseEta: true,
          rcBranch: 'releases/mozilla-beta',
          disableable: true,
        },
        {
          prettyName: 'Try',
          project: 'try',
          branch: 'try',
          repo: 'https://hg.mozilla.org/try',
          enableReleaseEta: false,
          disableable: true,
        },
      ],
      enablePartials: true,
    },
    {
      product: 'fennec',
      prettyName: 'Firefox Mobile',
      // TODO: The actual appName is `mobile/android` but it gets the version from `browser`.
      appName: 'browser',
      branches: [
        {
          prettyName: 'Maple Beta',
          project: 'maple',
          branch: 'projects/maple',
          repo: 'https://hg.mozilla.org/projects/maple',
          enableReleaseEta: false,
          disableable: false,
        },
      ],
      enablePartials: false,
    },
    {
      product: 'devedition',
      prettyName: 'Firefox Developer Edition',
      appName: 'browser',
      branches: [
        {
          prettyName: 'Maple Beta',
          project: 'maple',
          branch: 'projects/maple',
          repo: 'https://hg.mozilla.org/projects/maple',
          enableReleaseEta: false,
          disableable: true,
        },
      ],
      enablePartials: true,
    },
    {
      product: 'thunderbird',
      prettyName: 'Thunderbird',
      appName: 'mail',
      branches: [
        {
          prettyName: 'Try',
          project: 'try-comm-central',
          branch: 'try-comm-central',
          repo: 'https://hg.mozilla.org/try-comm-central',
          enableReleaseEta: false,
          disableable: false,
        },
      ],
      // TODO
      enablePartials: false,
    },
  ],
  XPI_PRODUCTS: [
    {
      product: 'xpi',
      prettyName: 'Click to load manifest',
      branch: 'master',
      owner: 'escapewindow',
      repo: 'test-xpi-manifest',
    },
  ],
};

