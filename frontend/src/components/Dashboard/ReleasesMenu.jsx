import { withAuth0 } from '@auth0/auth0-react';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import Typography from '@mui/material/Typography';
import MenuDownIcon from 'mdi-react/MenuDownIcon';
import RocketLaunchIcon from 'mdi-react/RocketLaunchIcon';
import React, { Fragment, useState } from 'react';
import { makeStyles } from 'tss-react/mui';
import Link from '../../utils/Link';
import menuItems from './menuItems';

export function hasChildren(item) {
  const { items: children } = item;

  if (children === undefined) {
    return false;
  }

  if (children.constructor !== Array) {
    return false;
  }

  if (children.length === 0) {
    return false;
  }

  return true;
}

const useStyles = makeStyles()(() => ({
  button: {
    color: '#fff',
    display: 'flex',
    textTransform: 'none',
    marginRight: '.15%',
  },
  endIcon: {
    margin: '0px',
  },
  listItemLink: {
    textDecoration: 'none',
    color: 'inherit',
  },
}));
const SingleLevel = withAuth0(({ item, disabled, auth0 }) => {
  const { classes } = useStyles();

  if ((!auth0.user || disabled) && item.to.includes('new')) {
    return '';
  }

  return (
    <Link
      key={item.title}
      nav
      to={item.to ? item.to : ''}
      className={classes.listItemLink}
    >
      <ListItemButton>
        <ListItemIcon style={{ minWidth: '30px' }}>{item.Icon}</ListItemIcon>
        <ListItemText primary={item.title} />
      </ListItemButton>
    </Link>
  );
});
const MultiLevel = ({ item }) => {
  const { items: children } = item;
  const [open, setOpen] = useState(false);
  const handleClick = () => {
    setOpen((prev) => !prev);
  };

  return (
    <React.Fragment>
      <ListItemButton onClick={handleClick}>
        <ListItemText primary={item.title} />
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          {children.map((child) => (
            <MenuItem key={`${item.title}-${child.title}`} item={child} />
          ))}
        </List>
      </Collapse>
    </React.Fragment>
  );
};

const MenuItem = ({ item, disabled }) => {
  const Component = hasChildren(item) ? MultiLevel : SingleLevel;

  return <Component item={item} disabled={disabled} />;
};

function MenuItems({ disabled }) {
  return menuItems.map((item) => (
    <MenuItem key={item.title} item={item} disabled={disabled} />
  ));
}

function ReleasesMenu({ disabled }) {
  const { classes } = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  return (
    <Fragment>
      <Button
        className={classes.button}
        classes={{
          endIcon: classes.endIcon,
        }}
        aria-haspopup="true"
        aria-controls="user-menu"
        aria-label="user menu"
        startIcon={<RocketLaunchIcon />}
        endIcon={<MenuDownIcon />}
        onClick={handleMenuOpen}
      >
        <Typography variant="h6" noWrap>
          Releases
        </Typography>
      </Button>
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}
        className={classes.menu}
        slotProps={{
          root: { sx: { '.MuiList-root': { padding: 0 } } },
        }}
      >
        <MenuItems disabled={disabled} />
      </Menu>
    </Fragment>
  );
}

export default ReleasesMenu;
