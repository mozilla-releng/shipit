import axios from 'axios';
import config from '../config';
import { extractGithubRepoOwnerAndName, getPushes, isGitHubRepo } from './vcs';

const prettyNames = Object.fromEntries(
  Object.values(config.PRODUCTS)
    .flat()
    .map((p) => [p.product, p.prettyName]),
);

export function prettyProductName(productKey) {
  return (
    prettyNames[productKey] ||
    productKey.charAt(0).toUpperCase() + productKey.slice(1)
  );
}

export async function getMergeAutomationProducts() {
  const req = await axios.get('/merge-automation/products');
  return req.data;
}

export async function getMergeBehaviors(product) {
  const url = `/merge-automation/behaviors/${product}`;
  const req = await axios.get(url, { authRequired: true });

  // [{behavior, ...}] -> {behavior: {...}}
  return Object.fromEntries(req.data.map((b) => [b.behavior, b]));
}

async function getHgCommitInfo(repoUrl, revision, signal) {
  const url = `${repoUrl}/json-log?rev=${revision}`;
  const req = await axios.get(url, { signal });
  const commitData = req.data.entries[0];

  return {
    desc: commitData.desc,
    author: commitData.user,
    node: commitData.node,
    date: commitData.date[0],
  };
}

async function getHgVersion(repoUrl, revision, versionPath, signal) {
  const url = `${repoUrl}/raw-file/${revision}/${versionPath}`;
  const req = await axios.get(url, {
    transformResponse: [(data) => data],
    signal,
  });

  return req.data.trim();
}

export async function getMergeRevisions(behaviorConfig, signal) {
  const pushes = await getPushes(
    behaviorConfig.repo,
    behaviorConfig.branch,
    signal,
  );

  const commits = Object.fromEntries(pushes.map((push) => [push.node, push]));

  if (behaviorConfig['always-target-tip']) {
    const firstKey = Object.keys(commits)[0];
    if (firstKey) {
      return { [firstKey]: commits[firstKey] };
    }
  }

  return commits;
}

export async function getMergeInfo(
  behaviorConfig,
  revision,
  signal,
  commitData,
) {
  let version;
  let commitInfo;

  if (isGitHubRepo(behaviorConfig.repo)) {
    const { repoOwner, repoName } = extractGithubRepoOwnerAndName(
      behaviorConfig.repo,
    );

    const versionRes = await axios.get(
      `/github/file/${repoOwner}/${repoName}/${revision}`,
      {
        authRequired: true,
        params: { path: behaviorConfig.version_path },
        transformResponse: [(data) => data],
        signal,
      },
    );

    version = versionRes.data.trim();
    commitInfo = {
      desc: commitData ? commitData.desc : '',
      author: commitData ? commitData.author : '',
    };
  } else {
    [version, commitInfo] = await Promise.all([
      getHgVersion(
        behaviorConfig.repo,
        revision,
        behaviorConfig.version_path,
        signal,
      ),
      getHgCommitInfo(behaviorConfig.repo, revision, signal),
    ]);
  }

  return {
    version,
    commit_message: commitInfo.desc.split('\n')[0],
    commit_author: commitInfo.author,
  };
}

export async function submitMergeAutomation(
  product,
  behavior,
  revision,
  dryRun,
  version,
  commitMessage,
  commitAuthor,
) {
  const mergeAutomationObj = {
    product,
    behavior,
    revision,
    dryRun,
    version,
    commitMessage,
    commitAuthor,
  };

  const req = await axios.post('/merge-automation', mergeAutomationObj, {
    authRequired: true,
  });

  return req.data;
}

export async function getMergeAutomations(product) {
  const url = `/merge-automation?product=${product}`;
  const req = await axios.get(url);

  return req.data;
}

export async function cancelMergeAutomation(automationId) {
  const url = `/merge-automation/${automationId}`;
  const req = await axios.delete(url, { authRequired: true });

  return req.data;
}

export async function startMergeAutomation(automationId) {
  const url = `/merge-automation/${automationId}/start`;
  const req = await axios.post(url, {}, { authRequired: true });

  return req.data;
}

export async function getMergeAutomationTaskStatus(automationId) {
  const url = `/merge-automation/${automationId}/task-status`;
  const req = await axios.get(url, { authRequired: true });

  return req.data;
}
