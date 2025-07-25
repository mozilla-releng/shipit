import { Auth0Context } from '@auth0/auth0-react';
import AppBar from '@material-ui/core/AppBar';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import { makeStyles } from '@material-ui/core/styles';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import CancelOutlinedIcon from '@material-ui/icons/CancelOutlined';
import CheckCircleOutlineIcon from '@material-ui/icons/CheckCircleOutline';
import HourglassEmptyIcon from '@material-ui/icons/HourglassEmpty';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import React, { Fragment, useContext, useState } from 'react';

const useStyles = makeStyles(() => ({
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
  const classes = useStyles();
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
          <Typography color="inherit" variant="subtitle1" noWrap>
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
                  color={pb.disabled ? 'secondary' : 'default'}
                >
                  {getIcon(loading, pb.disabled)}
                </Button>
              ) : (
                <Button
                  style={{ minWidth: '30px', padding: '0px' }}
                  disabled
                  color={pb.disabled ? 'secondary' : 'default'}
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
                  {loading && <Spinner loading />}
                  <Button
                    variant="contained"
                    onClick={closeModal}
                    color="default"
                    autoFocus
                  >
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
