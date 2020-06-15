import React, { useEffect } from 'react';
import Button from '@material-ui/core/Button';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import Grid from '@material-ui/core/Grid';
import Dashboard from '../../components/Dashboard';
import {
  getPendingReleases,
  getRecentReleases,
  getRecentXPIReleases,
} from '../../components/api';
import useAction from '../../hooks/useAction';
import ReleaseProgress from '../../components/ReleaseProgress';
import ReleaseContext from '../../utils/ReleaseContext';
import config from '../../config';

export default function Releases({ recent = false, xpi = false }) {
  let releaseFetcher = null;

  if (xpi) {
    // XPI release fetchers
    if (recent) {
      // read-only, aka recent releases
      releaseFetcher = getRecentXPIReleases;
    } else {
      // releases in progress
      releaseFetcher = () =>
        getPendingReleases('/xpi/releases', '/xpi/signoff', false);
    }
  } else if (recent) {
    // releases in progress
    // A list of all product/branch variants:
    // [[product, branch], [product, branch]]
    const productBranches = config.PRODUCTS.map(p => [
      p.branches.map(b => [p.product, b.branch]),
    ])
      .flatMap(x => x)
      .flatMap(x => x);

    releaseFetcher = () => getRecentReleases(productBranches);
  } else {
    // read-only, aka recent releases
    releaseFetcher = getPendingReleases;
  }

  const [releases, fetchReleases] = useAction(releaseFetcher);

  useEffect(() => {
    fetchReleases();
  }, []);

  return (
    <ReleaseContext.Provider value={{ fetchReleases }}>
      <Dashboard title={recent ? 'Recent Releases' : 'Pending Releases'}>
        <Grid container justify="flex-end">
          <Button onClick={async () => fetchReleases()}>Refresh</Button>
        </Grid>
        {releases.loading && <Spinner loading />}

        {releases.data && releases.data.length < 1 && (
          <h2>No {recent ? 'recent' : 'pending'} releases</h2>
        )}
        {releases.data &&
          releases.data.map(release => (
            <ReleaseProgress
              release={release}
              key={release.name}
              readOnly={recent}
              xpi={xpi}
            />
          ))}
      </Dashboard>
    </ReleaseContext.Provider>
  );
}
