import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import React from 'react';
import { render } from 'react-dom';
import App from './App';

const root = document.getElementById('root');
// To stop the footer from covering content
root.style.paddingBottom = '52.6px';
const load = () => {
  render(
    <App />,
    root,
  );
};

load();
