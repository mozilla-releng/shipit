import Box from '@material-ui/core/Box';
import Button from '@material-ui/core/Button';
import CircularProgress from '@material-ui/core/CircularProgress';
import RefreshIcon from 'mdi-react/RefreshIcon';
import React, { useEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import {
  getPendingReleases,
  getPendingReleasesForProductBranches,
  getRecentReleases,
  getRecentXPIReleases,
} from '../../components/api';
import Dashboard from '../../components/Dashboard';
import ErrorPanel from '../../components/ErrorPanel';
import ReleaseProgress from '../../components/ReleaseProgress';
import { getXpis } from '../../components/vcs';
import config from '../../config';
import useAction from '../../hooks/useAction';
import ReleaseContext from '../../utils/ReleaseContext';

function getProductBranches(group) {
  if (!(group in config.PRODUCTS)) return [];

  // A list of all product/branch variants:
  // [[product, branch], [product, branch]]
  return config.PRODUCTS[group]
    .flatMap((p) => [p.branches.map((b) => [p.product, b.branch])])
    .flat();
}

export default function Releases({ recent = false, xpi = false }) {
  const location = useLocation();
  const group = new URLSearchParams(location.search).get('group') || 'firefox';
  const groupTitle = group.charAt(0).toUpperCase() + group.slice(1);
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
    // read-only, aka recent releases
    releaseFetcher = (productBranches) => getRecentReleases(productBranches);
  } else {
    // releases in progress
    releaseFetcher = (productBranches) =>
      getPendingReleasesForProductBranches(productBranches);
  }

  const [releases, fetchReleases] = useAction(releaseFetcher);
  const [xpis, fetchXpis] = useAction(xpiFetcher);

  useEffect(() => {
    if (xpi) {
      fetchReleases();
      fetchXpis();
    } else {
      const productBranches = getProductBranches(group);

      fetchReleases(productBranches);
    }
  }, [group]);

  if (!(group in config.PRODUCTS)) {
    return (
      <BrowserRouter>
        <Dashboard disabled>
          <ErrorPanel fixed error={`Unknown group: ${group}.`} />
        </Dashboard>
      </BrowserRouter>
    );
  }

  const productBranches = xpi ? undefined : getProductBranches(group);

  return (
    <ReleaseContext.Provider value={{ fetchReleases, productBranches }}>
      <Dashboard
        group={xpi ? 'Extensions' : groupTitle}
        title={recent ? 'Recent Releases' : 'Pending Releases'}
      >
        <Box
          display="flex"
          justifyContent="right"
          alignItems="right"
          marginRight="1%"
        >
          <Button
            startIcon={<RefreshIcon />}
            onClick={async () => fetchReleases(productBranches)}
          >
            Refresh
          </Button>
        </Box>
        {(releases.loading || (xpi && xpis.loading)) && (
          <Box style={{ textAlign: 'center' }}>
            <CircularProgress loading />
          </Box>
        )}

        {releases.data && releases.data.length < 1 && (
          <h2>No {recent ? 'recent' : 'pending'} releases</h2>
        )}
        {(xpi ? xpis?.data : true) &&
          releases.data &&
          releases.data.map((release) => (
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
