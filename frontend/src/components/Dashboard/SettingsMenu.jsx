import React, { useState, Fragment } from 'react';
import Button from '@material-ui/core/Button';
import { makeStyles } from '@material-ui/styles';
import Menu from '@material-ui/core/Menu';
import ListItem from '@material-ui/core/ListItem';
import SettingsOutlineIcon from 'mdi-react/SettingsOutlineIcon';
import MenuDownIcon from 'mdi-react/MenuDownIcon';
import ListItemText from '@material-ui/core/ListItemText';
import Typography from '@material-ui/core/Typography';
import Spinner from '@mozilla-frontend-infra/components/Spinner';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import UpdateIcon from '@material-ui/icons/Update';
import { ListItemIcon } from '@material-ui/core';
import LinkVariantIcon from 'mdi-react/LinkVariantIcon';
import Link from '../../utils/Link';
import { withUser } from '../../utils/AuthContext';
import { rebuildProductDetails } from '../api';
import useAction from '../../hooks/useAction';

const useStyles = makeStyles(theme => ({
  button: {
    color: '#fff',
    display: 'flex',
    textTransform: 'none',
    marginRight: '.15%',
  },
  endIcon: {
    margin: '0px',
  },
  icon: {
    fill: '#fff',
  },
  link: {
    ...theme.mixins.link,
  },
  listItemLink: {
    textDecoration: 'none',
    color: 'inherit',
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
      {!user || disabled ? (
        ''
      ) : (
        <Button
          className={classes.button}
          classes={{
            endIcon: classes.endIcon,
          }}
          aria-haspopup="true"
          aria-controls="user-menu"
          aria-label="user menu"
          startIcon={<SettingsOutlineIcon className={classes.icon} />}
          endIcon={<MenuDownIcon className={classes.icon} />}
          onClick={handleMenuOpen}>
          <Typography color="inherit" variant="h6" noWrap>
            Settings
          </Typography>
        </Button>
      )}
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        getContentAnchorEl={null}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}>
        <ListItem button>
          <ListItemIcon style={{ minWidth: '30px' }}>
            <UpdateIcon />
          </ListItemIcon>
          <ListItemText
            primary="Update product details"
            onClick={() => setShowModal(true)}
          />
        </ListItem>
        <Link
          nav
          to="https://product-details.mozilla.org/1.0/"
          className={classes.listItemLink}>
          <ListItem button>
            <ListItemIcon style={{ minWidth: '30px' }}>
              <LinkVariantIcon />
            </ListItemIcon>
            <ListItemText primary="Go to product details" />
          </ListItem>
        </Link>
      </Menu>
      <Dialog open={showModal} onClose={() => setShowModal(false)}>
        <DialogTitle id="alert-dialog-title">
          Update product details?
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
            Update
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  );
}

export default withUser(SettingsMenu);
