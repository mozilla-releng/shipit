import React, { useState, Fragment } from "react";
import Button from "@material-ui/core/Button";
import { makeStyles } from "@material-ui/styles";
import Menu from "@material-ui/core/Menu";
import menuItems from './menuItems';
import { withUser } from "../../utils/AuthContext";
import SettingsOutlineIcon from "mdi-react/RocketIcon";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
// import ListItemIcon from "@material-ui/core/ListItemIcon";
import ListItemText from "@material-ui/core/ListItemText";
import Collapse from "@material-ui/core/Collapse";
import ExpandLessIcon from "@material-ui/icons/ExpandLess";
import ExpandMoreIcon from "@material-ui/icons/ExpandMore";

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

const MenuItem = ({ item }) => {
  const Component = hasChildren(item) ? MultiLevel : SingleLevel;
  return <Component item={item} />;
};

const SingleLevel = ({ item }) => {
  const classes = useStyles();
  return (
    <ListItem button className={classes.singleLevel}>
      <ListItemText primary={item.title} />
    </ListItem>
  );
};

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
          {children.map((child, key) => (
            <MenuItem key={key} item={child} />
          ))}
        </List>
      </Collapse>
    </React.Fragment>
  );
};

const useStyles = makeStyles((theme) => ({
  button: {
    color: '#fff',
    display: 'flex',
  },
  singleLevel: {
    paddingLeft: '40px',
  },
  menu: {
    // width: '100%',
    // padding: '10%'
  }
}));

function MenuItems() {
  return menuItems.map((item, key) => <MenuItem key={key} item={item} />);
}

function SettingsMenu({ user, disabled }) {
  const classes = useStyles();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  return (
    <Fragment>
      <Button
        disabled={!user || disabled}
        className={classes.button}
        aria-haspopup="true"
        aria-controls="user-menu"
        aria-label="user menu"
        startIcon={<SettingsOutlineIcon />}
        onClick={handleMenuOpen}
      >
        Releases
      </Button>
      <Menu
        id="user-menu"
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        getContentAnchorEl={null}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        onClose={handleMenuClose}
        className={classes.menu}
      >
        <MenuItems />
      </Menu>
    </Fragment>
  );
}

export default withUser(SettingsMenu);
