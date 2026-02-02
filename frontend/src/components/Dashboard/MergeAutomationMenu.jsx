import { AddBox, List } from '@mui/icons-material';
import SettingsOutlineIcon from '@mui/icons-material/MergeOutlined';
import React, { useEffect, useState } from 'react';
import {
  getMergeAutomationProducts,
  prettyProductName,
} from '../merge_automation';
import DashboardMenu from './DashboardMenu';
import { ExpandableSection, LinkMenuItem } from './MenuComponents';

function ProductSection({ product, displayName, defaultOpen = false }) {
  return (
    <ExpandableSection title={displayName} defaultOpen={defaultOpen}>
      <LinkMenuItem
        icon={<AddBox />}
        text="New"
        to={`/merge-automation/new?product=${product}`}
      />
      <LinkMenuItem
        icon={<List />}
        text="List"
        to={`/merge-automation?product=${product}`}
      />
    </ExpandableSection>
  );
}

function MergeAutomationMenu({ disabled }) {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    if (disabled) return;
    getMergeAutomationProducts().then(setProducts);
  }, [disabled]);

  return (
    <DashboardMenu
      title="Merge Automation"
      icon={<SettingsOutlineIcon />}
      menuId="merge-automation-menu"
      ariaLabel="merge automation menu"
      disabled={disabled}
    >
      {products.map((product, index) => (
        <ProductSection
          key={product}
          product={product}
          displayName={prettyProductName(product)}
          defaultOpen={index === 0}
        />
      ))}
    </DashboardMenu>
  );
}

export default MergeAutomationMenu;
