function isHgRepo(repo) {
  return repo.startsWith('https://hg.mozilla.org/');
}

function isGitHubRepo(repo) {
  return repo.startsWith('https://github.com/');
}

function checkRepoIsSupported(repo) {
  if (!(isHgRepo(repo) || isGitHubRepo(repo))) {
    throw Error(`Unsupported repo: ${repo}`);
  }
}

function extractGithubRepoOwnerAndName(repo) {
  const parsedUrl = new URL(repo);
  const path = parsedUrl.pathname;
  const parts = path.split('/');
  return { repoOwner: parts[1], repoName: parts[2] };
}

function getPushesUrl(repo, branch) {
  checkRepoIsSupported(repo);

  let url;
  if (isHgRepo(repo)) {
    url = `${repo}/json-pushes?version=2&full=1&tipsonly=1`;
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);
    url = `https://api.github.com/repos/${repoOwner}/${repoName}/commits?sha=${branch}`;
  }

  return url;
}

function getRawFileUrl(repo, revision, filePath) {
  checkRepoIsSupported(repo);

  let url;
  if (isHgRepo(repo)) {
    url = `${repo}/raw-file/${revision}/${filePath}`;
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);
    // Calling https://github.com/${repoOwner}/${repoName}/raw/ doesn't work because of CORS.
    // Github only allows https://render.githubcontent.com as `Access-Control-Allow-Origin`.
    url = `https://raw.githubusercontent.com/${repoOwner}/${repoName}/${revision}/${filePath}`;
  }

  return url;
}

/**
 * Get latest pushes.
 */
export async function getPushes(repo, branch) {
  const url = getPushesUrl(repo, branch);
  const req = await fetch(url);
  const rawData = await req.json();

  let latestPushes;
  if (isHgRepo(repo)) {
    latestPushes = Object.values(rawData.pushes).map(push =>
      ({ ...push.changesets[0], date: new Date(push.date * 1000) })).reverse();
  } else if (isGitHubRepo(repo)) {
    latestPushes = rawData.map(commit => ({
      date: new Date(commit.commit.committer.date),
      node: commit.sha,
      desc: commit.commit.message,
    }));
  }
  return latestPushes;
}

/**
 * Get in-tree product "display" version.
 */
export async function getVersion(repo, revision, appName, versionFile) {
  const versionFilePath = versionFile || `${appName}/config/version_display.txt`;
  const url = getRawFileUrl(repo, revision, versionFilePath);
  const res = await fetch(url);
  if (res.ok) {
    const version = await res.text();
    return version.trim();
  }
  return '';
}

/**
 * Get in-tree "shipped" locales.
 */
export async function getLocales(repo, revision, appName) {
  const localesFilePath = `${appName}/locales/l10n-changesets.json`;
  const url = getRawFileUrl(repo, revision, localesFilePath);
  const res = await fetch(url);
  const locales = await res.json();
  return Object.keys(locales);
}
