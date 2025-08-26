import { ListItemIcon } from '@mui/material';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React from 'react';
import { makeStyles } from 'tss-react/mui';
import Link from '../../utils/Link';

const useStyles = makeStyles()(() => ({
  listItemLink: {
    textDecoration: 'none',
    color: 'inherit',
  },
}));

export function ActionMenuItem({ icon, text, onClick }) {
  return (
    <ListItemButton onClick={onClick}>
      <ListItemIcon style={{ minWidth: '30px' }}>{icon}</ListItemIcon>
      <ListItemText primary={text} />
    </ListItemButton>
  );
}

export function LinkMenuItem({ icon, text, to }) {
  const { classes } = useStyles();

  return (
    <Link nav to={to} className={classes.listItemLink}>
      <ListItemButton>
        <ListItemIcon style={{ minWidth: '30px' }}>{icon}</ListItemIcon>
        <ListItemText primary={text} />
      </ListItemButton>
    </Link>
  );
}
