import { createTheme } from '@material-ui/core/styles';
// import '../node_modules/@mozilla-protocol/core/protocol/css/protocol.css';
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
      fontFamily: "'Inter', sans-serif",
    },
    button: {
      fontFamily: "'Inter', sans-serif",
    },
    overline: {
      fontFamily: "'Inter', sans-serif",
    }
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
