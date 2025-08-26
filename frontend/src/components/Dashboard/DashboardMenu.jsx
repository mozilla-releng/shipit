import { withAuth0 } from '@auth0/auth0-react';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import Typography from '@mui/material/Typography';
import React, { Fragment, useEffect, useState } from 'react';
import { useLocation } from 'react-router';
import { makeStyles } from 'tss-react/mui';

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
  icon: {
    fill: '#fff',
  },
}));

function DashboardMenu({
  title,
  icon,
  children,
  disabled,
  ariaLabel,
  menuId,
  auth0,
}) {
  const { classes } = useStyles();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);
  const handleMenuOpen = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  useEffect(() => {
    setAnchorEl(null);
  }, [location]);

  if (!auth0.user || disabled) {
    return '';
  }

  return (
    <Fragment>
      <Button
        className={classes.button}
        classes={{
          endIcon: classes.endIcon,
        }}
        aria-haspopup="true"
        aria-controls={menuId}
        aria-label={ariaLabel || title.toLowerCase()}
        startIcon={React.cloneElement(icon, { className: classes.icon })}
        endIcon={<ArrowDropDownIcon className={classes.icon} />}
        onClick={handleMenuOpen}
      >
        <Typography variant="h6" noWrap>
          {title}
        </Typography>
      </Button>
      <Menu
        id={menuId}
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        onClose={handleMenuClose}
        slotProps={{
          root: { sx: { '.MuiList-root': { padding: 0 } } },
        }}
      >
        {children}
      </Menu>
    </Fragment>
  );
}

export default withAuth0(DashboardMenu);
