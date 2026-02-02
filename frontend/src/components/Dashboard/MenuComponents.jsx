import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { ListItemIcon } from '@mui/material';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import React, { useState } from 'react';
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

export function ExpandableSection({ title, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <React.Fragment>
      <ListItemButton onClick={() => setOpen((prev) => !prev)}>
        <ListItemText primary={title} />
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          {children}
        </List>
      </Collapse>
    </React.Fragment>
  );
}
