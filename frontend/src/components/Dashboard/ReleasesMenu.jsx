import { withAuth0 } from '@auth0/auth0-react';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import React from 'react';
import DashboardMenu from './DashboardMenu';
import { ExpandableSection, LinkMenuItem } from './MenuComponents';
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

  return (
    <ExpandableSection title={item.title}>
      {children.map((child) => (
        <MenuItem key={`${item.title}-${child.title}`} item={child} />
      ))}
    </ExpandableSection>
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
