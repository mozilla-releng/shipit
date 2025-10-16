import { AddBox, List } from '@mui/icons-material';
import SettingsOutlineIcon from '@mui/icons-material/MergeOutlined';
import React from 'react';
import DashboardMenu from './DashboardMenu';
import { LinkMenuItem } from './MenuComponents';

function MergeAutomationMenu({ disabled }) {
  return (
    <DashboardMenu
      title="Merge Automation"
      icon={<SettingsOutlineIcon />}
      menuId="merge-automation-menu"
      ariaLabel="merge automation menu"
      disabled={disabled}
    >
      <LinkMenuItem
        icon={<AddBox />}
        text="New merge automation"
        to="/merge-automation/new"
      />
      <LinkMenuItem
        icon={<List />}
        text="List merge automation"
        to="/merge-automation"
      />
    </DashboardMenu>
  );
}

export default MergeAutomationMenu;
