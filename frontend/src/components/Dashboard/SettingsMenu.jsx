import LinkIcon from '@mui/icons-material/Link';
import SettingsOutlineIcon from '@mui/icons-material/SettingsOutlined';
import UpdateIcon from '@mui/icons-material/Update';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import React, { Fragment, useState } from 'react';
import useAction from '../../hooks/useAction';
import { rebuildProductDetails } from '../api';
import DashboardMenu from './DashboardMenu';
import { ActionMenuItem, LinkMenuItem } from './MenuComponents';

function SettingsMenu({ disabled }) {
  const [showModal, setShowModal] = useState(false);
  const [rebuildProductDetailsState, rebuildProductDetailsAction] = useAction(
    rebuildProductDetails,
  );

  return (
    <Fragment>
      <DashboardMenu
        title="Settings"
        icon={<SettingsOutlineIcon />}
        menuId="settings-menu"
        ariaLabel="settings menu"
        disabled={disabled}
      >
        <ActionMenuItem
          icon={<UpdateIcon />}
          text="Update product details"
          onClick={() => setShowModal(true)}
        />
        <LinkMenuItem
          icon={<LinkIcon />}
          text="Go to product details"
          to="https://product-details.mozilla.org/1.0/"
        />
      </DashboardMenu>
      <Dialog open={showModal} onClose={() => setShowModal(false)}>
        <DialogTitle id="alert-dialog-title">
          Update Product Details
        </DialogTitle>
        <DialogContent>
          {rebuildProductDetailsState.error ? (
            <p>{rebuildProductDetailsState.error.toString()}</p>
          ) : (
            'Do you want to update the products details API?'
          )}
        </DialogContent>
        <DialogActions>
          {rebuildProductDetailsState.loading && <CircularProgress />}
          <Button
            variant="contained"
            onClick={() => setShowModal(false)}
            autoFocus
          >
            Close
          </Button>
          <Button
            disabled={rebuildProductDetailsState.loading}
            variant="contained"
            onClick={async () => {
              await rebuildProductDetailsAction();
              setShowModal(false);
            }}
            color="primary"
          >
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export default SettingsMenu;
