import { withAuth0 } from '@auth0/auth0-react';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React, { useState } from 'react';
import DashboardMenu from './DashboardMenu';
import { LinkMenuItem } from './MenuComponents';
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

const SingleLevel = withAuth0(({ item, disabled, auth0 }) => {
  if ((!auth0.user || disabled) && item.to.includes('new')) {
    return '';
  }

  return (
    <LinkMenuItem
      key={item.title}
      icon={item.Icon}
      text={item.title}
      to={item.to || ''}
    />
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
  return (
    <DashboardMenu
      title="Releases"
      icon={<RocketLaunchIcon />}
      menuId="releases-menu"
      ariaLabel="releases menu"
      disabled={disabled}
    >
      <MenuItems disabled={disabled} />
    </DashboardMenu>
  );
}

export default ReleasesMenu;
