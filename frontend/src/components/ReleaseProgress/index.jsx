import { Auth0Context } from '@auth0/auth0-react';
import AndroidIcon from '@mui/icons-material/Android';
import CancelIcon from '@mui/icons-material/Block';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import React, { useContext, useState } from 'react';
import { useLocation } from 'react-router';
import { makeStyles } from 'tss-react/mui';
import config from '../../config';
import useAction from '../../hooks/useAction';
import { repoUrlBuilder } from '../../utils/helpers';
import ReleaseContext from '../../utils/ReleaseContext';
import { cancelRelease as cancelReleaseAPI } from '../api';
import PhaseProgress from '../PhaseProgress';

const useStyles = makeStyles()((theme) => ({
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
  const { classes } = useStyles();
  const authContext = useContext(Auth0Context);
  const mutable = authContext.user && !readOnly;
  const [open, setOpen] = useState(false);
  const [cancelState, cancelAction] = useAction(cancelReleaseAPI);
  const { fetchReleases, productBranches } = useContext(ReleaseContext);
  const releaseCancelled =
    cancelState.data !== null && !cancelState.error && !cancelState.loading;
  const handleClose = () => {
    setOpen(false);
  };

  const cancelRelease = async (releaseName) => {
    const result = await cancelAction(
      releaseName,
      xpi ? '/xpi/releases' : '/releases',
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
          color="secondary"
        >
          Cancel
        </Button>
        <Dialog open={open} onClose={handleClose}>
          <DialogTitle>Cancel Release</DialogTitle>
          <DialogContent>{renderDialogContent()}</DialogContent>
          <DialogActions>
            {cancelState.loading && <CircularProgress />}
            <Button onClick={handleClose} variant="contained">
              Close
            </Button>
            <Button
              onClick={() => cancelRelease(release.name)}
              variant="contained"
              disabled={releaseCancelled || cancelState.loading}
              color="secondary"
            >
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
    const product = PRODUCTS?.[group].find(
      (product) => product.product === release.product,
    );

    if (product?.branches) {
      productBranch = product.branches.find(
        (item) =>
          item.branch === release.branch && item.project === release.project,
      );
    }

    // non-hg or firefox projects are formatted differently in the config files
    if (!productBranch && product && product.repositories) {
      productBranch = product.repositories.find(
        (item) => item.project === release.product,
      );
    }

    if (isXPI) {
      enableTreeherder = false;
      trimmedRevision = release.xpi_revision.substring(0, 13);
      let repo = '';
      let owner = '';

      xpis.data.xpis.forEach((xpi) => {
        if (xpi.xpi_name === release.xpi_name) {
          repo = xpi.repo;
          owner = xpi.owner;
        }
      });

      url = repoUrlBuilder(
        `https://github.com/${owner}/${repo}`,
        release.xpi_revision,
      );
    } else if (productBranch?.repo) {
      url = repoUrlBuilder(productBranch.repo, release.revision);
      enableTreeherder = productBranch.enableTreeherder !== false;
    }

    return (
      <React.Fragment>
        {url ? (
          <Link target="_blank" href={url} underline="hover">
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
              href={`${TREEHERDER_URL}/jobs?repo=${release.project}&revision=${release.revision}`}
              underline="hover"
            >
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
        <Box typography="caption" display="block">
          Created on {dateCreated} with {renderReleaseTitle(xpi, release)}
        </Box>
        <Box sx={{ position: 'relative' }}>
          <Box sx={{ width: '50%', position: 'absolute' }}>
            {release.name.toLowerCase().includes('android') && (
              <AndroidIcon
                sx={{
                  color: '#20ac5f',
                  height: '1.5em',
                  width: '1.5em',
                }}
              />
            )}
          </Box>
        </Box>
        <PhaseProgress release={release} readOnly={!mutable} xpi={xpi} />
      </CardContent>
      <CardActions className={classes.cardActions}>
        {mutable && renderCancel()}
      </CardActions>
    </Card>
  );
}
