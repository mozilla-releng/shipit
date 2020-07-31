import React, { useState, Fragment } from 'react';
import Button from '@material-ui/core/Button';
import { makeStyles } from '@material-ui/styles';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import IconButton from '@material-ui/core/IconButton';
import SettingsOutlineIcon from 'mdi-react/SettingsOutlineIcon';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import { withUser } from '../../utils/AuthContext';
import { rebuildProductDetails } from '../api';
import useAction from '../../hooks/useAction';

const useStyles = makeStyles(theme => ({
  settings: {
    height: theme.spacing(6),
    width: theme.spacing(6),
    padding: 0,
    margin: `0 ${theme.spacing(1)}px`,
  },
  settingsIcon: {
    fill: '#fff',
  },
  settingsIconDisabled: {
    fill: theme.palette.grey[500],
  },
  link: {
    ...theme.mixins.link,
  },
}));

function SettingsMenu({ user, disabled }) {
  const classes = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = e => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const [showModal, setShowModal] = useState(false);
  const [rebuildProductDetailsState, rebuildProductDetailsAction] = useAction(
    rebuildProductDetails
  );

  return (
    <Fragment>
      <IconButton
        disabled={!user || disabled}
        className={classes.settings}
        aria-haspopup="true"
        aria-controls="user-menu"
        aria-label="user menu"
        onClick={handleMenuOpen}>
        <SettingsOutlineIcon
          size={24}
          className={
            user && !disabled
              ? classes.settingsIcon
              : classes.settingsIconDisabled
          }
        />
      </IconButton>
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        getContentAnchorEl={null}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}>
        <MenuItem
          dense
          key="rebuild"
          title="Rebuild product-details"
          onClick={() => setShowModal(true)}>
          Rebuild prooduct-details
        </MenuItem>
      </Menu>
      <Dialog open={showModal} onClose={() => setShowModal(false)}>
        <DialogTitle id="alert-dialog-title">
          Rebuild product details?
        </DialogTitle>
        <DialogContent>
          {rebuildProductDetailsState.error && (
            <p>{rebuildProductDetailsState.error.toString()}</p>
          )}
        </DialogContent>
        <DialogActions>
          {rebuildProductDetailsState.loading && <Spinner loading />}
          <Button
            variant="contained"
            onClick={() => setShowModal(false)}
            color="default"
            autoFocus>
            Close
          </Button>
          <Button
            disabled={rebuildProductDetailsState.loading}
            variant="contained"
            onClick={async () => {
              await rebuildProductDetailsAction();
              setShowModal(false);
            }}
            color="primary">
            Rebuild
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export default withUser(SettingsMenu);
