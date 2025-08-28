import { withAuth0 } from '@auth0/auth0-react';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import Avatar from '@mui/material/Avatar';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import React, { Fragment, useState } from 'react';
import { makeStyles } from 'tss-react/mui';
import Button from '../Button';

const useStyles = makeStyles()((theme) => ({
  avatar: {
    height: theme.spacing(6),
    width: theme.spacing(6),
    padding: 0,
  },
}));

function UserMenu(props) {
  const { auth0 } = props;
  const { classes } = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const handleLogoutClick = () => {
    handleMenuClose();
    auth0.logout({
      openUrl: false,
    });
  };

  const handleCopyAccessToken = async () => {
    const accessToken = await auth0.getAccessTokenSilently();

    await navigator.clipboard.writeText(accessToken);
    handleMenuClose();
  };

  const handleLogin = auth0.loginWithPopup;

  function avatarFromName(name) {
    const initials = name
      .split(' ')
      .slice(0, 2)
      .map((part) => part[0])
      .join('');
    return (
      <Avatar sx={{ backgroundColor: '#16a085', fontSize: '1rem' }} alt={name}>
        {initials}
      </Avatar>
    );
  }

  return (
    <Fragment>
      {auth0.isAuthenticated ? (
        <IconButton
          className={classes.avatar}
          aria-haspopup="true"
          aria-controls="user-menu"
          aria-label="user menu"
          onClick={handleMenuOpen}
          size="large"
        >
          {avatarFromName(auth0.user.name)}
        </IconButton>
      ) : (
        <Button
          onClick={handleLogin}
          size="small"
          variant="contained"
          color="secondary"
        >
          Login
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
        <MenuItem title="Copy Access Token" onClick={handleCopyAccessToken}>
          <ContentCopyIcon />
          Copy Access Token
        </MenuItem>
        <MenuItem title="Logout" onClick={handleLogoutClick}>
          <ExitToAppIcon />
          Logout
        </MenuItem>
      </Menu>
    </Fragment>
  );
}

export default withAuth0(UserMenu);
