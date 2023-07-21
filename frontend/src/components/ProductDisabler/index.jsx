import React, { Fragment, useState, useContext } from 'react';
import AppBar from '@material-ui/core/AppBar';
import Button from '@material-ui/core/Button';
import { makeStyles } from '@material-ui/core/styles';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import Typography from '@material-ui/core/Typography';
import HourglassEmptyIcon from '@material-ui/icons/HourglassEmpty';
import CancelOutlinedIcon from '@material-ui/icons/CancelOutlined';
import CheckCircleOutlineIcon from '@material-ui/icons/CheckCircleOutline';
import Toolbar from '@material-ui/core/Toolbar';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import { AuthContext } from '../../utils/AuthContext';

const useStyles = makeStyles(() => ({
  appBar: {
    top: 'auto',
    bottom: 0,
  },
  products: {
    paddingLeft: '5px',
    paddingRight: '5px',
  },
}));

export default function ProductDisabler({
  productBranches,
  loading,
  onStateChange,
  error,
}) {
  const classes = useStyles();
  const authContext = useContext(AuthContext);
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

  const openModal = pb => {
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
        <Typography color="inherit" variant="subtitle1" noWrap>
          Automated Release Status
        </Typography>
        {productBranches.map(pb => (
          <Fragment key={`${pb.product}-${pb.branch}`}>
            <Typography className={classes.products}>
              ┃ {pb.prettyProduct}: {pb.prettyBranch}
            </Typography>
            {mutable ? (
              <Button
                onClick={() => openModal(pb)}
                disabled={loading}
                color={pb.disabled ? 'secondary' : 'default'}>
                {getIcon(loading, pb.disabled)}
              </Button>
            ) : (
              getIcon(loading, pb.disabled)
            )}
          </Fragment>
        ))}

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
                    autoFocus>
                    Close
                  </Button>
                  <Button
                    disabled={loading}
                    variant="contained"
                    onClick={async () => {
                      await onStateChange(modalItem);
                      closeModal();
                    }}
                    color="primary">
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
