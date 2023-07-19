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
import { getXpis } from '../../components/vcs';

export default function Releases({ recent = false, xpi = false }) {
  let releaseFetcher = null;
  let xpiFetcher = () => null;

  if (xpi) {
    const { owner, project } = config.XPI_MANIFEST;

    xpiFetcher = async () => getXpis(owner, project, 'HEAD');

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
  const [xpis, fetchXpis] = useAction(xpiFetcher);

  useEffect(() => {
    fetchReleases();
    fetchXpis();
  }, []);

  return (
    <ReleaseContext.Provider value={{ fetchReleases }}>
      <Dashboard
        group={xpi ? 'Mozilla Extensions' : 'Firefox Products'}
        title={recent ? 'Recent Releases' : 'Pending Releases'}>
        <Grid container>
          <Button onClick={async () => fetchReleases()}>Refresh</Button>
        </Grid>
        {(releases.loading || (xpi && xpis.loading)) && <Spinner loading />}

        {releases.data && releases.data.length < 1 && (
          <h2>No {recent ? 'recent' : 'pending'} releases</h2>
        )}
        {(xpi ? xpis && xpis.data : true) &&
          releases.data &&
          releases.data.map(release => (
            <ReleaseProgress
              release={release}
              key={release.name}
              readOnly={recent}
              xpi={xpi}
              xpis={xpis}
            />
          ))}
      </Dashboard>
    </ReleaseContext.Provider>
  );
}
