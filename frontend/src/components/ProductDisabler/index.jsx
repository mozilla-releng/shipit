import { Auth0Context } from '@auth0/auth0-react';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import AppBar from '@mui/material/AppBar';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import React, { Fragment, useContext, useState } from 'react';
import { makeStyles } from 'tss-react/mui';

const useStyles = makeStyles()(() => ({
  appBar: {
    top: 'auto',
    bottom: 0,
  },
  title: {
    color: '#fff',
  },
}));

export default function ProductDisabler({
  productBranches,
  loading,
  onStateChange,
  error,
}) {
  const { classes } = useStyles();
  const authContext = useContext(Auth0Context);
  const mutable = authContext.user;
  const [showModal, setShowModal] = useState(false);
  const [modalItem, setModalItem] = useState(null);
  const getIcon = (loading, disabled) => {
    if (loading) {
      return <HourglassEmptyIcon style={{ fill: '#fff' }} />;
    }

    if (disabled) {
      return <CancelOutlinedIcon style={{ fill: '#fff' }} />;
    }

    return <CheckCircleOutlineIcon style={{ fill: '#fff' }} />;
  };

  const openModal = (pb) => {
    setShowModal(true);
    setModalItem(pb);
  };

  const closeModal = () => {
    setShowModal(false);
    setModalItem(null);
  };

  /* productBranches looks like:

       [
         {
           "product": "firefox",
           "branch": "mozilla-beta",
           "prettyProduct": "Firefox Desktop",
           "prettyBranch": "Beta",
           "disabled": true,
         }
       ],
       ...
    */

  return (
    <AppBar position="fixed" className={classes.appBar}>
      <Toolbar>
        <Breadcrumbs
          aria-label="breadcrumb"
          separator="|"
          className={classes.title}
        >
          <Typography variant="subtitle1" noWrap>
            Automated Release Status
          </Typography>
          {productBranches.map((pb) => (
            <Typography
              color="inherit"
              variant="subtitle1"
              noWrap
              className={classes.products}
              key={`${pb.product}-${pb.branch}`}
            >
              {pb.prettyProduct}: {pb.prettyBranch}
              {mutable ? (
                <Button
                  style={{ minWidth: '30px', padding: '0px' }}
                  onClick={() => openModal(pb)}
                  disabled={loading}
                  color={pb.disabled ? 'secondary' : 'inherit'}
                >
                  {getIcon(loading, pb.disabled)}
                </Button>
              ) : (
                <Button
                  style={{ minWidth: '30px', padding: '0px' }}
                  disabled
                  color={pb.disabled ? 'secondary' : 'inherit'}
                >
                  {getIcon(loading, pb.disabled)}
                </Button>
              )}
            </Typography>
          ))}
        </Breadcrumbs>

        {mutable && (
          <Dialog open={showModal} onClose={closeModal}>
            {modalItem && (
              <Fragment>
                <DialogTitle id="alert-dialog-title">
                  {modalItem.disabled ? 'Enable' : 'Disable'} automated releases
                  of {modalItem.prettyProduct} {modalItem.prettyBranch}?
                </DialogTitle>
                <DialogContent>
                  {error && <p>{error.toString()}</p>}
                </DialogContent>
                <DialogActions>
                  {loading && <CircularProgress />}
                  <Button variant="contained" onClick={closeModal} autoFocus>
                    Close
                  </Button>
                  <Button
                    disabled={loading}
                    variant="contained"
                    onClick={async () => {
                      await onStateChange(modalItem);
                      closeModal();
                    }}
                    color="primary"
                  >
                    {modalItem.disabled ? 'Enable' : 'Disable'}
                  </Button>
                </DialogActions>
              </Fragment>
            )}
          </Dialog>
        )}
      </Toolbar>
    </AppBar>
  );
}
