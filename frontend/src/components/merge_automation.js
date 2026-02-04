import axios from 'axios';
import config from '../config';

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

async function getHgPushes(repo, alwaysTargetTip) {
  const url = `${repo}/json-pushes?version=2&full=1&tipsonly=1&branch=default`;
  const req = await axios.get(url);

  const commits = {};
  const pushes = req.data.pushes;

  Object.values(pushes).forEach((push) => {
    push.changesets.forEach((changeset) => {
      commits[changeset.node] = {
        date: new Date(push.date * 1000),
        desc: changeset.desc,
        author: changeset.author,
      };
    });
  });

  if (alwaysTargetTip) {
    const firstKey = Object.keys(commits)[0];

    if (firstKey) {
      return { [firstKey]: commits[firstKey] };
    }
  }

  return commits;
}

async function getHgCommitInfo(repoUrl, revision) {
  const url = `${repoUrl}/json-log?rev=${revision}`;
  const req = await axios.get(url);
  const commitData = req.data.entries[0];

  return {
    desc: commitData.desc,
    author: commitData.user,
    node: commitData.node,
    date: commitData.date[0],
  };
}

async function getHgVersion(repoUrl, revision, versionPath) {
  const url = `${repoUrl}/raw-file/${revision}/${versionPath}`;
  const req = await axios.get(url, {
    transformResponse: [(data) => data],
  });

  return req.data.trim();
}

export async function getMergeRevisions(behaviorConfig, signal) {
  const pushes = await getHgPushes(
    behaviorConfig.repo,
    behaviorConfig['always-target-tip'],
  );

  return pushes;
}

export async function getMergeInfo(behaviorConfig, revision, signal) {
  const [version, commitInfo] = await Promise.all([
    getHgVersion(behaviorConfig.repo, revision, behaviorConfig.version_path),
    getHgCommitInfo(behaviorConfig.repo, revision),
  ]);

  const commitMessage = commitInfo.desc.split('\n')[0];

  return {
    version,
    commit_message: commitMessage,
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
