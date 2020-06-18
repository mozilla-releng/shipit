module.exports = {
  TASKCLUSTER_ROOT_URL: 'https://firefox-ci-tc.services.mozilla.com',
  TREEHERDER_URL: 'https://treeherder.mozilla.org',
  AUTH0: {
    domain: 'auth.mozilla.auth0.com',
    clientID: 'FK1mJkHhwjulTYBGklxn8W4Fhd1pgT4t',
    redirectUri: new URL('/login', window.location).href,
    scope: 'full-user-credentials openid profile email',
    responseType: 'token id_token',
    audience: 'https://auth.mozilla.auth0.com/api/v2/',
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
      canTogglePartials: true,
    },
    {
      product: 'fennec',
      prettyName: 'Firefox Mobile',
      // TODO: The actual appName is `mobile/android` but it gets the version
      // from `browser`.
      appName: 'browser',
      branches: [
        {
          prettyName: 'Maple Beta',
          project: 'maple',
          branch: 'projects/maple',
          repo: 'https://hg.mozilla.org/projects/maple',
          enableReleaseEta: false,
          alternativeBranch: 'releases/mozilla-beta',
          disableable: false,
        },
        {
          prettyName: 'Try',
          project: 'try',
          branch: 'try',
          repo: 'https://hg.mozilla.org/try',
          enableReleaseEta: false,
          disableable: false,
        },
        {
          prettyName: 'Try Release',
          project: 'maple',
          branch: 'try',
          repo: 'https://hg.mozilla.org/try',
          enableReleaseEta: false,
          productKey: 'fennec_release',
          versionFile:
            'mobile/android/config/version-files/release/version_display.txt',
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
      canTogglePartials: true,
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
      enablePartials: true,
      canTogglePartials: true,
    },
    {
      product: 'fenix',
      prettyName: 'Fenix',
      appName: 'fenix',
      repositories: [
        {
          prettyName: "Johan's fork",
          project: 'fenix',
          repo: 'https://github.com/JohanLorenzo/fenix',
          enableReleaseEta: false,
        },
      ],
      enablePartials: false,
    },
  ],
  XPI_MANIFEST: {
    branch: 'master',
    owner: 'escapewindow',
    repo: 'test-xpi-manifest',
  },
};
