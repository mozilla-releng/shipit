import { withAuth0 } from '@auth0/auth0-react';
import Button from '@material-ui/core/Button';
import Collapse from '@material-ui/core/Collapse';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import Menu from '@material-ui/core/Menu';
import Typography from '@material-ui/core/Typography';
import ExpandLessIcon from '@material-ui/icons/ExpandLess';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import { makeStyles } from '@material-ui/styles';
import MenuDownIcon from 'mdi-react/MenuDownIcon';
import RocketIcon from 'mdi-react/RocketIcon';
import React, { Fragment, useState } from 'react';
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

const useStyles = makeStyles(() => ({
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
  const classes = useStyles();

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
      <ListItem button>
        <ListItemIcon style={{ minWidth: '30px' }}>{item.Icon}</ListItemIcon>
        <ListItemText primary={item.title} />
      </ListItem>
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
      <ListItem button onClick={handleClick}>
        <ListItemText primary={item.title} />
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItem>
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
  const classes = useStyles();
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
        startIcon={<RocketIcon />}
        endIcon={<MenuDownIcon />}
        onClick={handleMenuOpen}
      >
        <Typography color="inherit" variant="h6" noWrap>
          Releases
        </Typography>
      </Button>
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        getContentAnchorEl={null}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}
        className={classes.menu}
      >
        <MenuItems disabled={disabled} />
      </Menu>
    </Fragment>
  );
}

export default ReleasesMenu;
