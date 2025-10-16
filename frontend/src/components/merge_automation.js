import axios from 'axios';

export async function getMergeBehaviors(product) {
  const url = `/merge-automation/behaviors/${product}`;
  const req = await axios.get(url, { authRequired: true });

  return req.data;
}

export async function getMergeRevisions(product, behavior, signal) {
  const url = `/merge-automation/${product}/${behavior}`;
  const req = await axios.get(url, { authRequired: true, signal });

  const data = req.data;

  Object.keys(data).forEach((key) => {
    if (data[key].date) {
      data[key].date = new Date(data[key].date * 1000);
    }
  });

  return data;
}

export async function getMergeInfo(product, behavior, revision, signal) {
  const url = `/merge-automation/${product}/${behavior}/${revision}`;
  const req = await axios.get(url, { authRequired: true, signal });

  return req.data;
}

export async function submitMergeAutomation(
  product,
  behavior,
  revision,
  dryRun,
) {
  const mergeAutomationObj = {
    product,
    behavior,
    revision,
    dryRun,
  };

  const req = await axios.post('/merge-automation', mergeAutomationObj, {
    authRequired: true,
  });

  return req.data;
}

export async function getMergeAutomations(product) {
  const url = `/merge-automation?product=${product}`;
  const req = await axios.get(url, { authRequired: true });

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
