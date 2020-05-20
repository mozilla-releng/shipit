import axios from 'axios';

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

export async function getGithubCommits(repoOwner, repoName, branch) {
  const url = `/github/commits/${repoOwner}/${repoName}/${branch}`;
  const req = await axios.get(url, { authRequired: true });

  return req.data;
}

export async function getXpis(owner, repo, commit) {
  const url = `/github/xpis/${owner}/${repo}/${commit}`;
  const req = await axios.get(url, { authRequired: true });

  return req.data;
}

export async function getXPIVersion(owner, repo, commit) {
  const url = `/github/package_json/${owner}/${repo}/${commit}`;
  const req = await axios.get(url, { authRequired: true });

  return req.data.version;
}

async function getHgPushes(repo) {
  const url = `${repo}/json-pushes?version=2&full=1&tipsonly=1`;
  const req = await axios.get(url);

  return req.data;
}

/**
 * Get latest pushes.
 */
export async function getPushes(repo, branch) {
  checkRepoIsSupported(repo);

  let latestPushes;

  if (isHgRepo(repo)) {
    const rawData = await getHgPushes(repo);

    latestPushes = Object.values(rawData.pushes)
      .map(push => ({
        ...push.changesets[0],
        date: new Date(push.date * 1000),
      }))
      .reverse();
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);
    const rawData = await getGithubCommits(repoOwner, repoName, branch);

    latestPushes = rawData.map(commit => ({
      date: new Date(commit.committer_date),
      node: commit.revision,
      desc: commit.message,
    }));
  }

  return latestPushes;
}

/**
 * Get in-tree product "display" version.
 */
export async function getVersion(repo, revision, appName, versionFile) {
  checkRepoIsSupported(repo);

  let url;
  let authRequired = false;

  if (isHgRepo(repo)) {
    const versionFilePath =
      versionFile || `${appName}/config/version_display.txt`;

    url = `${repo}/raw-file/${revision}/${versionFilePath}`;
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);

    url = `/github/version_txt/${repoOwner}/${repoName}/${revision}`;
    authRequired = true;
  }

  const res = await axios.get(url, { authRequired });

  if (res.status === 200) {
    const version = res.data;

    return version.trim();
  }

  return '';
}

/**
 * Get in-tree "shipped" locales.
 */
export async function getLocales(repo, revision, appName) {
  const localesFilePath = `${appName}/locales/l10n-changesets.json`;
  const url = `${repo}/raw-file/${revision}/${localesFilePath}`;
  const res = await axios.get(url);
  const locales = res.data;

  return Object.keys(locales);
}
