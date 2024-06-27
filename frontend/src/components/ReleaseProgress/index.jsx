import React, { useState, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import Box from '@material-ui/core/Box';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import CancelIcon from 'mdi-react/CancelIcon';
import AndroidIcon from 'mdi-react/AndroidIcon';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import CardActions from '@material-ui/core/CardActions';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import Link from '@material-ui/core/Link';
import { makeStyles } from '@material-ui/styles';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import PhaseProgress from '../PhaseProgress';
import { cancelRelease as cancelReleaseAPI } from '../api';
import useAction from '../../hooks/useAction';
import ReleaseContext from '../../utils/ReleaseContext';
import { AuthContext } from '../../utils/AuthContext';
import config from '../../config';
import { repoUrlBuilder } from '../../utils/helpers';

const useStyles = makeStyles(theme => ({
  cardActions: {
    justifyContent: 'flex-end',
  },
  releaseCard: {
    margin: '1%',
    border: `1px solid ${theme.palette.grey[400]}`,
    backgroundColor: theme.palette.background.paper,
  },
  icon: {
    fill: theme.palette.secondary.main,
  },
  startIcon: {
    marginRight: '5px',
  },
}));

export default function ReleaseProgress({
  release,
  readOnly = false,
  xpi = false,
  xpis = null,
}) {
  const location = useLocation();
  const group = new URLSearchParams(location.search).get('group') || 'firefox';
  const classes = useStyles();
  const authContext = useContext(AuthContext);
  const mutable = authContext.user && !readOnly;
  const [open, setOpen] = useState(false);
  const [cancelState, cancelAction] = useAction(cancelReleaseAPI);
  const { fetchReleases, productBranches } = useContext(ReleaseContext);
  const releaseCancelled =
    cancelState.data !== null && !cancelState.error && !cancelState.loading;
  const handleClose = () => {
    setOpen(false);
  };

  const cancelRelease = async releaseName => {
    const result = await cancelAction(
      releaseName,
      xpi ? '/xpi/releases' : '/releases'
    );

    if (!result.error) {
      await handleClose();
      await fetchReleases(productBranches);
    }
  };

  const renderDialogContent = () => {
    if (cancelState.error) {
      return <p>{cancelState.error.toString()}</p>;
    }

    return <p>Do you want to cancel {release.name}?</p>;
  };

  const renderCancel = () => {
    return (
      <React.Fragment>
        <Button
          classes={{
            startIcon: classes.startIcon,
          }}
          startIcon={<CancelIcon className={classes.icon} />}
          onClick={() => setOpen(true)}
          color="secondary">
          Cancel
        </Button>
        <Dialog open={open} onClose={handleClose}>
          <DialogTitle>Cancel Release</DialogTitle>
          <DialogContent>{renderDialogContent()}</DialogContent>
          <DialogActions>
            {cancelState.loading && <Spinner loading />}
            <Button onClick={handleClose} variant="contained" color="default">
              Close
            </Button>
            <Button
              onClick={() => cancelRelease(release.name)}
              variant="contained"
              disabled={releaseCancelled || cancelState.loading}
              color="secondary">
              Cancel
            </Button>
          </DialogActions>
        </Dialog>
      </React.Fragment>
    );
  };

  const renderReleaseTitle = (isXPI, release) => {
    let url = null;
    let productBranch = null;
    let enableTreeherder = true;
    const { PRODUCTS, TREEHERDER_URL } = config;
    let trimmedRevision = release.revision.substring(0, 13);
    const product =
      PRODUCTS &&
      PRODUCTS[group].find(product => product.product === release.product);

    if (product && product.branches) {
      productBranch = product.branches.find(
        item =>
          item.branch === release.branch && item.project === release.project
      );
    }

    // non-hg or firefox projects are formatted differently in the config files
    if (!productBranch && product && product.repositories) {
      productBranch = product.repositories.find(
        item => item.project === release.product
      );
    }

    if (isXPI) {
      enableTreeherder = false;
      trimmedRevision = release.xpi_revision.substring(0, 13);
      let repo = '';
      let owner = '';

      xpis.data.xpis.forEach(xpi => {
        if (xpi.xpi_name === release.xpi_name) {
          repo = xpi.repo;
          owner = xpi.owner;
        }
      });

      url = repoUrlBuilder(
        `https://github.com/${owner}/${repo}`,
        release.xpi_revision
      );
    } else if (productBranch && productBranch.repo) {
      url = repoUrlBuilder(productBranch.repo, release.revision);
      enableTreeherder = productBranch.enableTreeherder !== false;
    }

    return (
      <React.Fragment>
        {url ? (
          <Link target="_blank" href={url}>
            {trimmedRevision}
          </Link>
        ) : (
          trimmedRevision
        )}

        {enableTreeherder && TREEHERDER_URL && (
          <span>
            {' '}
            .{' '}
            <Link
              target="_blank"
              href={`${TREEHERDER_URL}/jobs?repo=${release.project}&revision=${release.revision}`}>
              View in Treeherder
            </Link>
          </span>
        )}
      </React.Fragment>
    );
  };

  const dateCreated = new Date(release.created).toUTCString();

  return (
    <Card key={release.name} className={classes.releaseCard} variant="outlined">
      <CardContent>
        <Typography component="h3" variant="h6">
          {release.name}
        </Typography>
        <Box fontSize=".85rem" fontWeight="fontWeightRegular" display="block">
          Created on {dateCreated} with {renderReleaseTitle(xpi, release)}
        </Box>
        <div style={{ position: 'relative' }}>
          <div style={{ width: '50%', position: 'absolute' }}>
            {release.name.toLowerCase().includes('android') && (
              <AndroidIcon
                style={{
                  color: '#20ac5f',
                  height: '2.5em',
                  width: '2.5em',
                  left: 0,
                  marginTop: '1em',
                }}
              />
            )}
          </div>
        </div>
        <PhaseProgress release={release} readOnly={!mutable} xpi={xpi} />
      </CardContent>
      <CardActions className={classes.cardActions}>
        {mutable && renderCancel()}
      </CardActions>
    </Card>
  );
}
