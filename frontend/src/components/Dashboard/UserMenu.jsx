import React, { useState, Fragment } from 'react';
import { makeStyles } from '@material-ui/styles';
import Avatar from '@material-ui/core/Avatar';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import IconButton from '@material-ui/core/IconButton';
import ExitToAppIcon from '@material-ui/icons/ExitToApp';
import Button from '../Button';
import { withUser } from '../../utils/AuthContext';

const useStyles = makeStyles(theme => ({
  avatar: {
    height: theme.spacing(6),
    width: theme.spacing(6),
    padding: 0,
  },
}));

function UserMenu(props) {
  const { user, onAuthorize, onUnauthorize } = props;
  const classes = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = e => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);
  const handleLogoutClick = () => {
    handleMenuClose();
    onUnauthorize();
  };

  return (
    <Fragment>
      {user ? (
        <IconButton
          className={classes.avatar}
          aria-haspopup="true"
          aria-controls="user-menu"
          aria-label="user menu"
          onClick={handleMenuOpen}>
          {user.picture ? (
            <Avatar alt={user.nickname} src={user.picture} />
          ) : (
            <Avatar alt={user.name}>{user.name[0]}</Avatar>
          )}
        </IconButton>
      ) : (
        <Button
          onClick={onAuthorize}
          size="small"
          variant="contained"
          color="secondary">
          Login
        </Button>
      )}
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        getContentAnchorEl={null}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}>
        <MenuItem title="Logout" onClick={handleLogoutClick}>
          <ExitToAppIcon />
          Logout
        </MenuItem>
      </Menu>
    </Fragment>
  );
}

export default withUser(UserMenu);
