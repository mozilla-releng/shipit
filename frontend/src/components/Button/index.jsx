import MuiButton from '@mui/material/Button';
import { red } from '@mui/material/colors';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { oneOf } from 'prop-types';
import React from 'react';

const dangerTheme = createTheme({
  palette: {
    primary: red,
  },
});

// A Material UI Button augmented with a danger color
function Button({ color = 'inherit', ...rest }) {
  if (color === 'danger') {
    return (
      <ThemeProvider theme={dangerTheme}>
        <MuiButton color="primary" {...rest} />
      </ThemeProvider>
    );
  }

  return <MuiButton color={color} {...rest} />;
}

Button.propTypes = {
  color: oneOf(['inherit', 'primary', 'secondary', 'danger']),
};

export default Button;
