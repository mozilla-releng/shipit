import React from 'react';
import Popover from '@material-ui/core/Popover';
import Box from '@material-ui/core/Box';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(theme => ({
  popover: {
    pointerEvents: 'none',
  },
  paper: {
    padding: theme.spacing(1),
  },
}));

export default function MouseOverPopover({
  popoverContent,
  text,
  fontSize,
  fontWeight,
  position,
  marginTop,
  marginLeft,
}) {
  const classes = useStyles();
  const [anchorEl, setAnchorEl] = React.useState(null);
  const handlePopoverOpen = event => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  return (
    <div>
      <Box
        aria-owns={open ? 'mouse-over-popover' : undefined}
        aria-haspopup="true"
        onMouseEnter={handlePopoverOpen}
        onMouseLeave={handlePopoverClose}
        fontSize={fontSize}
        fontWeight={fontWeight}
        marginTop={marginTop}
        marginLeft={marginLeft}
        position={position}>
        {text}
      </Box>
      <Popover
        id="mouse-over-popover"
        className={classes.popover}
        classes={{
          paper: classes.paper,
        }}
        open={open}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus>
        <Box>{popoverContent}</Box>
      </Popover>
    </div>
  );
}

MouseOverPopover.defaultProps = {
  position: 'relative',
};
