module.exports = {
  TASKCLUSTER_ROOT_URL: 'https://firefox-ci-tc.services.mozilla.com',
  TREEHERDER_URL: 'https://treeherder.mozilla.org',
  AUTH0: {
    domain: 'auth.mozilla.auth0.com',
    clientID: '2dXygwTNP3p7iLTSaEWbdoiJFkjSBqm4',
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
            prettyName: 'Beta',
            project: 'mozilla-beta',
            branch: 'releases/mozilla-beta',
            repo: 'https://hg.mozilla.org/releases/mozilla-beta',
            enableReleaseEta: false,
            disableable: true,
          },
          {
            prettyName: 'Release',
            project: 'mozilla-release',
            branch: 'releases/mozilla-release',
            repo: 'https://hg.mozilla.org/releases/mozilla-release',
            enableReleaseEta: true,
            rcBranch: 'releases/mozilla-beta',
            rcBranchVersionPattern: /b/,
            rcRepo: 'https://hg.mozilla.org/releases/mozilla-beta',
            numberOfPartials: 4,
            disableable: false,
          },
          {
            prettyName: 'ESR102',
            project: 'mozilla-esr102',
            branch: 'releases/mozilla-esr102',
            repo: 'https://hg.mozilla.org/releases/mozilla-esr102',
            enableReleaseEta: true,
            numberOfPartials: 5,
            disableable: false,
          },
          {
            prettyName: 'ESR115',
            project: 'mozilla-esr115',
            branch: 'releases/mozilla-esr115',
            repo: 'https://hg.mozilla.org/releases/mozilla-esr115',
            enableReleaseEta: true,
            numberOfPartials: 5,
            alternativeBranch: 'releases/mozilla-esr102',
            alternativeRepo: 'https://hg.mozilla.org/releases/mozilla-esr102',
            disableable: false,
          },
        ],
        enablePartials: true,
      },
      {
        product: 'devedition',
        prettyName: 'Firefox Developer Edition',
        appName: 'browser',
        branches: [
          {
            prettyName: 'Beta',
            project: 'mozilla-beta',
            branch: 'releases/mozilla-beta',
            repo: 'https://hg.mozilla.org/releases/mozilla-beta',
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
            prettyName: 'Beta',
            project: 'comm-beta',
            branch: 'releases/comm-beta',
            repo: 'https://hg.mozilla.org/releases/comm-beta',
            enableReleaseEta: false,
            disableable: false,
          },
          {
            prettyName: 'Release',
            project: 'comm-release',
            branch: 'releases/comm-release',
            repo: 'https://hg.mozilla.org/releases/comm-release',
            alternativeBranch: 'releases/comm-beta',
            alternativeRepo: 'https://hg.mozilla.org/releases/comm-beta',
            enableReleaseEta: false,
            disableable: false,
          },
          {
            prettyName: 'ESR115',
            project: 'comm-esr115',
            branch: 'releases/comm-esr115',
            repo: 'https://hg.mozilla.org/releases/comm-esr115',
            alternativeBranch: 'releases/comm-esr102',
            alternativeRepo: 'https://hg.mozilla.org/releases/comm-esr102',
            enableReleaseEta: false,
            disableable: false,
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
            branch: '',
          },
        ],
        repositories: [
          {
            prettyName: 'Android monorepo',
            project: 'firefox-android',
            repo: 'https://github.com/mozilla-mobile/firefox-android',
            enableReleaseEta: false,
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
            prettyName: 'Application Services',
            project: 'app-services',
            repo: 'https://github.com/mozilla/application-services',
            enableReleaseEta: false,
            enableTreeherder: false,
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
            prettyName: 'Mozilla VPN Client',
            project: 'mozilla-vpn-client',
            repo: 'https://github.com/mozilla-mobile/mozilla-vpn-client',
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
            prettyName: 'Mozilla VPN Client',
            project: 'mozilla-vpn-addons',
            repo: 'https://github.com/mozilla-mobile/mozilla-vpn-client',
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
    owner: 'mozilla-extensions',
    project: 'xpi-manifest',
    repo: 'https://github.com/mozilla-extensions/xpi-manifest',
  },
};
