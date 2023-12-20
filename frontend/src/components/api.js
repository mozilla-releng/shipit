import axios from 'axios';
import libUrls from 'taskcluster-lib-urls';
import { getLocales } from './vcs';
import isRc from './releases';
import config from '../config';

/**
 * Get build numbers from the API endpoint.
 *
 * This will fetch all release builds including shipped, aborted, and not
 * started yet.
 */
export async function getBuildNumbers(product, version) {
  const res = await axios.get('/releases', {
    params: { product, version, status: 'shipped,aborted,scheduled' },
    usePublicApi: true,
  });
  const releases = res.data;

  return releases.map(release => release.build_number);
}

/**
 * Get releases
 *
 * This will fetch releases for the given params. Params may optionally include
 * product, branch, version, buildNumber or status.
 */
export async function getReleases(
  params = null,
  url = '/releases',
  usePublicApi = true
) {
  const res = await axios.get(url, {
    params,
    usePublicApi,
  });

  return res.data.reverse();
}

/**
 * Get releases for product branches
 *
 * This will return all releases that match the given array of [product,
 * branch] tuples.
 */
export async function getReleasesForProductBranches(
  productBranches,
  params,
  limit = null,
  url = '/releases',
  usePublicApi = true
) {
  const releases = await Promise.all(
    productBranches.map(async ([product, branch]) => {
      const newParams = { ...params, product, branch };
      const releases = await getReleases(newParams, url, usePublicApi);

      return limit ? releases : releases.slice(0, limit);
    })
  );

  return releases.flatMap(x => x);
}

/**
 * Get shipped releases
 *
 * This will fetch only shipped releases for a specific branch-product
 * combination. Optionally the version can be specified.
 */
export async function getShippedReleases(
  product,
  branch,
  version = null,
  buildNumber = null
) {
  return getReleases({
    product,
    branch,
    version,
    build_number: buildNumber,
    status: 'shipped',
  });
}

export async function getRecentReleases(productBranches, limit = 4) {
  // [
  //   [ 'firefox', 'projects/maple' ],
  //   [ 'firefox', 'try' ],
  //   ...
  // ]
  const recentReleases = await getReleasesForProductBranches(
    productBranches,
    { status: 'shipped' },
    limit
  );

  return recentReleases.flatMap(x => x);
}

export async function getXPIBuildNumbers(xpiName, xpiVersion) {
  const releases = await getReleases(
    {
      xpi_name: xpiName,
      xpi_version: xpiVersion,
      status: 'shipped,aborted,scheduled',
    },
    '/xpi/releases'
  );

  return releases.map(release => release.build_number);
}

export async function getShippedXPIReleases() {
  const releases = await getReleases(
    {
      status: 'shipped',
    },
    '/xpi/releases'
  );

  return releases;
}

export async function getRecentXPIReleases(limit = 4) {
  const releases = await getShippedXPIReleases();

  return releases.slice(0, limit);
}

export async function guessBuildNumber(product, version) {
  const buildNumbers = await getBuildNumbers(product, version);
  const nextBuildNumber =
    buildNumbers.length !== 0 ? Math.max(...buildNumbers) + 1 : 1;

  return nextBuildNumber;
}

async function generatePartialUpdates(
  selectedProduct,
  selectedBranch,
  version,
  partialVersions
) {
  const { product } = selectedProduct;
  const {
    branch,
    repo,
    rcBranch,
    rcBranchVersionPattern,
    rcRepo,
    alternativeBranch,
    alternativeRepo,
  } = selectedBranch;
  const partialUpdates = await Promise.all(
    partialVersions
      // ignore empty values, generated by trailing commas and .split()
      .filter(x => x)
      .map(async ver => {
        const [partialVersion, buildNumber] = ver.split('build');
        let partialBranch = branch;
        let partialRepo = repo;

        // override the branch in case this is an RC and the version matches
        // the (beta) pattern
        if (
          isRc(version) &&
          rcBranch &&
          rcBranchVersionPattern.test(partialVersion)
        ) {
          partialBranch = rcBranch;
          partialRepo = rcRepo;
        }

        let shippedReleases = await getShippedReleases(
          product,
          partialBranch,
          partialVersion,
          buildNumber
        );

        if (shippedReleases.length === 0 && alternativeBranch) {
          partialBranch = alternativeBranch;
          partialRepo = alternativeRepo;
          shippedReleases = await getShippedReleases(
            product,
            partialBranch,
            partialVersion,
            buildNumber
          );
        }

        if (shippedReleases.length !== 1) {
          throw new Error(
            `Cannot obtain proper information for ${product} ${partialBranch} ${partialVersion} build ${buildNumber}`
          );
        }

        const { revision } = shippedReleases[0];
        const locales = await getLocales(
          partialRepo,
          revision,
          selectedProduct.appName
        );

        return [
          partialVersion,
          { buildNumber: parseInt(buildNumber, 10), locales },
        ];
      })
  );

  // flatten and convert to expected JSON format
  return Object.fromEntries(partialUpdates);
}

export async function submitRelease(
  selectedProduct,
  selectedBranch,
  revision,
  releaseEta,
  partialVersions,
  version,
  buildNumber
) {
  const { product } = selectedProduct;
  const { branch, repo, productKey } = selectedBranch;
  const releaseObj = {
    branch,
    build_number: buildNumber,
    product,
    repo_url: repo,
    revision,
    version,
  };

  if (releaseEta) {
    releaseObj.release_eta = releaseEta.toISOString();
  }

  if (selectedProduct.enablePartials) {
    releaseObj.partial_updates = await generatePartialUpdates(
      selectedProduct,
      selectedBranch,
      version,
      partialVersions
    );
  }

  if (productKey) {
    releaseObj.product_key = productKey;
  }

  const req = await axios.post('/releases', releaseObj, {
    authRequired: true,
  });

  return req.data;
}

export async function guessPartialVersions(
  selectedProduct,
  selectedBranch,
  version
) {
  const { product } = selectedProduct;
  const {
    branch,
    rcBranch,
    numberOfPartials,
    alternativeBranch,
  } = selectedBranch;
  const numberOfPartialsOrDefault = numberOfPartials || 3;
  const shippedReleases = await getShippedReleases(product, branch);
  const shippedBuilds = shippedReleases.map(
    r => `${r.version}build${r.build_number}`
  );
  // take first N releases
  const suggestedBuilds = shippedBuilds.slice(0, numberOfPartialsOrDefault);
  // alternativeBranch is used for find partials from a different branch, and
  // usually used for ESR releases
  let suggestedAlternativeBuilds = [];

  if (suggestedBuilds.length < numberOfPartialsOrDefault && alternativeBranch) {
    const alternativeReleases = await getShippedReleases(
      product,
      alternativeBranch
    );
    const shippedAlternativeBuilds = alternativeReleases.map(
      r => `${r.version}build${r.build_number}`
    );

    suggestedAlternativeBuilds = shippedAlternativeBuilds.slice(
      0,
      numberOfPartialsOrDefault - suggestedBuilds.length
    );
  }

  // if RC, also add last shipped beta
  let suggestedRcBuilds = [];

  if (rcBranch && isRc(version)) {
    const rcShippedReleases = await getShippedReleases(product, rcBranch);
    const rcLastBuild = `${rcShippedReleases[0].version}build${rcShippedReleases[0].build_number}`;

    suggestedRcBuilds = [rcLastBuild];
  }

  return suggestedBuilds.concat(suggestedRcBuilds, suggestedAlternativeBuilds);
}

async function getTaskStatus(taskId) {
  const url = libUrls.api(
    config.TASKCLUSTER_ROOT_URL,
    'queue',
    'v1',
    `/task/${taskId}/status`
  );

  try {
    const req = await axios.get(url);

    return req.data;
  } catch (error) {
    return null;
  }
}

async function getTaskGroup(taskId) {
  const url = libUrls.api(
    config.TASKCLUSTER_ROOT_URL,
    'queue',
    'v1',
    `/task-group/${taskId}/list`
  );

  try {
    const req = await axios.get(url);

    return req.data;
  } catch (error) {
    return null;
  }
}

async function getTcStatus(phase) {
  const inProgress = ['unscheduled', 'pending', 'running'];
  const isError = ['failed', 'exception'];
  // This is the status of the phase's decision/action task
  const status = await getTaskStatus(phase.actionTaskId);

  // Only get the TC status for non-expired tasks
  if (!status) {
    return null;
  }

  // If the decision task is completed, we can check the task graph's task group
  if (status.status.state === 'completed') {
    const taskGroup = await getTaskGroup(phase.actionTaskId);

    if (taskGroup) {
      const statuses = taskGroup.tasks.map(task => task.status.state);

      // If there are errors the phase failed
      if (statuses.some(status => isError.includes(status))) {
        return 'warning';
      }

      // If there are no errors but
      // some tasks are in progress the phase is running
      if (statuses.some(status => inProgress.includes(status))) {
        return 'running';
      }

      // If all the tasks in the task graph completed the phase is complete
      if (statuses.every(status => status === 'completed')) {
        return 'completed';
      }
    }
  }

  return status.status.state;
}

async function getPhaseSignOffs(releaseName, phaseName, url = '/signoff') {
  const req = await axios.get(`${url}/${releaseName}/${phaseName}`);

  return req.data.signoffs;
}

async function getStatus(release, phase) {
  const isXPIRelease = 'xpi_name' in release;

  if (isXPIRelease) {
    return getTcStatus(phase);
  }

  const status = await getTaskStatus(phase.actionTaskId);

  if (!status) {
    return null; // expired?
  }

  return status.status.state;
}

export async function getPendingReleases(
  url = '/releases',
  signoffUrl = '/signoff',
  usePublicApi = true,
  params = null
) {
  const releases = await getReleases(params, url, usePublicApi);
  const pendingReleases = await Promise.all(
    releases.map(async release => {
      const phasesWithStatuses = await Promise.all(
        release.phases.map(async phase => {
          const signoffs = await getPhaseSignOffs(
            release.name,
            phase.name,
            signoffUrl
          );

          if (phase.submitted && phase.actionTaskId) {
            const tcStatus = await getStatus(release, phase);

            if (tcStatus) {
              // Only update the TC status for not expired tasks
              return { ...phase, tcStatus, signoffs };
            }

            return { ...phase, signoffs };
          }

          return { ...phase, signoffs };
        })
      );

      return { ...release, phases: phasesWithStatuses };
    })
  );

  return pendingReleases;
}

export async function getPendingReleasesForProductBranches(productBranches) {
  const pendingReleases = await Promise.all(
    productBranches.map(async ([product, branch]) => {
      return getPendingReleases('/releases', '/signoff', true, {
        product,
        branch,
      });
    })
  );

  return pendingReleases.flatMap(x => x);
}

export async function schedulePhase(releaseName, phaseName, url) {
  const req = await axios.put(
    `${url}/${releaseName}/${phaseName}`,
    {},
    {
      authRequired: true,
    }
  );

  return req.data;
}

export async function cancelRelease(releaseName, url) {
  const req = await axios.delete(`${url}/${releaseName}`, {
    authRequired: true,
  });

  return req.data;
}

export async function phaseSignOff(releaseName, phaseName, signoffUID, url) {
  const req = await axios.put(
    `${url}/${releaseName}/${phaseName}`,
    // The UID is sent as a quoted string, what requires the headers to be set
    // explicitly
    JSON.stringify(signoffUID),
    { authRequired: true, headers: { 'content-type': 'application/json' } }
  );

  return req.data;
}

export async function getDisabledProducts() {
  const req = await axios.get('/disabled-products', { usePublicApi: true });

  return req.data;
}

export async function disableProduct(product, branch) {
  const req = await axios.post(
    '/disabled-products',
    { product, branch },
    {
      authRequired: true,
    }
  );

  return req.data;
}

export async function enableProduct(product, branch) {
  const req = await axios.delete('/disabled-products', {
    authRequired: true,
    params: { product, branch },
  });

  return req.data;
}

export async function submitXPIRelease(
  manifestRevision,
  xpiRevision,
  xpiName,
  xpiVersion,
  buildNumber
) {
  const releaseObj = {
    revision: manifestRevision,
    xpi_revision: xpiRevision,
    xpi_name: xpiName,
    xpi_version: xpiVersion,
    build_number: buildNumber,
  };
  const req = await axios.post('/xpi/releases', releaseObj, {
    authRequired: true,
  });

  return req.data;
}

export async function rebuildProductDetails() {
  const req = await axios.post(
    '/product-details',
    {},
    {
      authRequired: true,
    }
  );

  return req.data;
}
