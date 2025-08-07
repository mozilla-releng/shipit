import { withAuth0 } from '@auth0/auth0-react';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import LinkIcon from '@mui/icons-material/Link';
import SettingsOutlineIcon from '@mui/icons-material/SettingsOutlined';
import UpdateIcon from '@mui/icons-material/Update';
import { ListItemIcon } from '@mui/material';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import Typography from '@mui/material/Typography';
import React, { Fragment, useState } from 'react';
import { makeStyles } from 'tss-react/mui';
import useAction from '../../hooks/useAction';
import Link from '../../utils/Link';
import { rebuildProductDetails } from '../api';

const useStyles = makeStyles()((theme) => ({
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

function SettingsMenu({ auth0, disabled }) {
  const { classes } = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const [showModal, setShowModal] = useState(false);
  const [rebuildProductDetailsState, rebuildProductDetailsAction] = useAction(
    rebuildProductDetails,
  );

  return (
    <Fragment>
      {!auth0.user || disabled ? (
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
          endIcon={<ArrowDropDownIcon className={classes.icon} />}
          onClick={handleMenuOpen}
        >
          <Typography variant="h6" noWrap>
            Settings
          </Typography>
        </Button>
      )}
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}
        slotProps={{
          root: { sx: { '.MuiList-root': { padding: 0 } } },
        }}
      >
        <ListItemButton>
          <ListItemIcon style={{ minWidth: '30px' }}>
            <UpdateIcon />
          </ListItemIcon>
          <ListItemText
            primary="Update product details"
            onClick={() => setShowModal(true)}
          />
        </ListItemButton>
        <Link
          nav
          to="https://product-details.mozilla.org/1.0/"
          className={classes.listItemLink}
        >
          <ListItemButton>
            <ListItemIcon style={{ minWidth: '30px' }}>
              <LinkIcon />
            </ListItemIcon>
            <ListItemText primary="Go to product details" />
          </ListItemButton>
        </Link>
      </Menu>
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

export default withAuth0(SettingsMenu);
