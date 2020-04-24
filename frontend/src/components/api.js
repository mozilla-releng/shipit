import { SHIPIT_API_URL, SHIPIT_PUBLIC_API_URL } from '../config';

/**
 * Get build numbers from the API endpoint.
 *
 * This will fetch all release builds including shipped, aborted, and not
 * started yet.
 */
export async function getBuildNumbers(product, branch, version) {
  const url = new URL(`${SHIPIT_PUBLIC_API_URL}/releases`);
  const params = new URLSearchParams({
    product,
    branch,
    version,
    status: 'shipped,aborted,scheduled',
  });
  url.search = params;
  const res = await fetch(url);
  const releases = await res.json();
  return releases.map(release => release.build_number);
}

/**
 * Get shipped releases
 *
 * This will fetch only shipped releases for a specific branch-product
 * combination. Optionally the version can be specified.
 */
export async function getShippedReleases(product, branch, version = null, buildNumber = null) {
  const url = new URL(`${SHIPIT_PUBLIC_API_URL}/releases`);
  const params = new URLSearchParams({
    product,
    branch,
    status: 'shipped',
  });
  if (version !== null) {
    params.set('version', version);
  }
  if (buildNumber !== null) {
    params.set('build_number', buildNumber);
  }
  url.search = params;
  const res = await fetch(url);
  const data = await res.json();
  return data.reverse();
}

export async function getXPIBuildNumbers(xpiName, xpiVersion) {
  const url = new URL(`${SHIPIT_API_URL}/xpi/releases`);
  const params = new URLSearchParams({
    xpi_name: xpiName,
    xpi_version: xpiVersion,
    status: 'shipped,aborted,scheduled',
  });
  url.search = params;
  const res = await fetch(url);
  const releases = await res.json();
  return releases.map(release => release.build_number);
}

export async function getShippedXPIReleases() {
  const url = new URL(`${SHIPIT_API_URL}/xpi/releases`);
  const params = new URLSearchParams({
    status: 'shipped',
  });
  url.search = params;
  const res = await fetch(url);
  const data = await res.json();
  return data.reverse();
}

export function getApiHeaders(accessToken) {
  return {
    Authorization: `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  };
}
