import { createTheme } from '@mui/material/styles';
import '../node_modules/@mozilla-protocol/core/protocol/css/protocol-components.css';

export default createTheme({
  overrides: {
    MuiList: {
      padding: {
        paddingTop: 0,
        paddingBottom: 0,
      },
    },
  },
  typography: {
    fontDisplay: 'swap',
    fontFamily: "'Zilla Slab', 'Inter', sans-serif",
    fontStyle: 'normal',
    fontWeight: 'normal',
    body1: {
      fontFamily: "'Inter', sans-serif",
    },
    body2: {
      fontFamily: "'Inter', sans-serif",
    },
    caption: {
      fontFamily: "'Roboto', sans-serif",
      fontWeight: 'normal',
      fontSize: '0.85rem',
    },
    button: {
      fontFamily: "'Inter', sans-serif",
    },
    overline: {
      fontFamily: "'Inter', sans-serif",
    },
  },
  palette: {
    primary: {
      main: '#000',
    },
    secondary: {
      main: '#c50042',
    },
    success: {
      main: '#3fe1b0',
      dark: '#008787',
    },
  },
});
