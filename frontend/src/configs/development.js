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
  PRODUCTS: {
    firefox: [
      {
        product: 'firefox',
        prettyName: 'Firefox Desktop',
        appName: 'browser',
        branches: [
          {
            prettyName: 'Try',
            project: 'try',
            branch: 'try',
            repo: 'https://hg.mozilla.org/try',
            enableReleaseEta: true,
            disableable: true,
          },
        ],
        enablePartials: true,
        canTogglePartials: true,
      },
      {
        product: 'devedition',
        prettyName: 'Firefox Developer Edition',
        appName: 'browser',
        branches: [
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
        product: 'firefox-android',
        prettyName: 'Firefox Android (Android-Components, Fenix, Focus)',
        appName: 'firefox-android',
        branches: [
          {
            prettyName: 'Try',
            project: 'try',
            branch: 'try',
            repo: 'https://hg.mozilla.org/try',
            enableReleaseEta: false,
            versionFile: 'mobile/android/version.txt',
            disableable: true,
          },
        ],
        enablePartials: false,
      },
      {
        product: 'firefox-ios',
        prettyName: 'Firefox iOS',
        appName: 'firefox-ios',
        branches: [
          {
            prettyName: 'Try',
            branch: '',
            disableable: true,
          },
        ],
        repositories: [
          {
            prettyName: 'Firefox iOS Staging',
            project: 'staging-firefox-ios',
            repo: 'https://github.com/mozilla-mobile/staging-firefox-ios',
            enableReleaseEta: false,
            enableTreeherder: true,
          },
        ],
        enablePartials: false,
      },
      {
        product: 'app-services',
        prettyName: 'Application Services',
        appName: 'app-services',
        branches: [
          {
            branch: '',
          },
        ],
        repositories: [
          {
            prettyName: 'Staging Application Services',
            project: 'app-services',
            repo: 'https://github.com/mozilla-releng/staging-application-services',
            enableReleaseEta: false,
            enableTreeherder: false,
          },
        ],
        enablePartials: false,
      },
    ],
    thunderbird: [
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
        enablePartials: false,
      },
    ],
    security: [
      {
        product: 'mozilla-vpn-client',
        prettyName: 'Mozilla VPN Client',
        appName: 'mozilla-vpn-client',
        branches: [
          {
            branch: '',
          },
        ],
        repositories: [
          {
            prettyName: 'Staging Mozilla VPN Client',
            project: 'mozilla-vpn-client',
            repo: 'https://github.com/mozilla-releng/staging-mozilla-vpn-client',
            enableReleaseEta: false,
            enableTreeherder: false,
          },
        ],
        enablePartials: false,
      },
      {
        product: 'mozilla-vpn-addons',
        prettyName: 'Mozilla VPN Addons',
        appName: 'mozilla-vpn-addons',
        branches: [
          {
            branch: '',
          },
        ],
        repositories: [
          {
            prettyName: 'Staging Mozilla VPN Client',
            project: 'mozilla-vpn-addons',
            repo: 'https://github.com/mozilla-releng/staging-mozilla-vpn-client',
            enableReleaseEta: false,
            enableTreeherder: false,
          },
        ],
        enablePartials: false,
      },
    ],
  },
  XPI_MANIFEST: {
    branch: 'main',
    owner: 'mozilla-releng',
    project: 'staging-xpi-manifest',
    repo: 'https://github.com/mozilla-releng/staging-xpi-manifest',
  },
};
