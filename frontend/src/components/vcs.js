import { SHIPIT_API_URL } from '../config';
import { getApiHeaders } from './api';


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

export async function getGithubCommits(repoOwner, repoName, branch, apiAccessToken) {
  const url = `${SHIPIT_API_URL}/github/commits/${repoOwner}/${repoName}/${branch}`;
  const req = await fetch(url, { headers: getApiHeaders(apiAccessToken) });
  return req.json();
}

async function getHgPushes(repo) {
  const url = `${repo}/json-pushes?version=2&full=1&tipsonly=1`;
  const req = await fetch(url);
  return req.json();
}

/**
 * Get latest pushes.
 */
export async function getPushes(repo, branch, apiAccessToken) {
  checkRepoIsSupported(repo);

  let latestPushes;
  if (isHgRepo(repo)) {
    const rawData = await getHgPushes(repo);
    latestPushes = Object.values(rawData.pushes).map(push =>
      ({ ...push.changesets[0], date: new Date(push.date * 1000) })).reverse();
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);
    const rawData = await getGithubCommits(repoOwner, repoName, branch, apiAccessToken);
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
export async function getVersion(repo, revision, appName, versionFile, apiAccessToken) {
  checkRepoIsSupported(repo);

  let url;
  let headers = {};
  if (isHgRepo(repo)) {
    const versionFilePath = versionFile || `${appName}/config/version_display.txt`;
    url = `${repo}/raw-file/${revision}/${versionFilePath}`;
  } else if (isGitHubRepo(repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(repo);
    url = `${SHIPIT_API_URL}/github/version_txt/${repoOwner}/${repoName}/${revision}`;
    headers = getApiHeaders(apiAccessToken);
  }

  const res = await fetch(url, { headers });
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
  const url = `${repo}/raw-file/${revision}/${localesFilePath}`;
  const res = await fetch(url);
  const locales = await res.json();
  return Object.keys(locales);
}
