import React from 'react';
import { render } from 'react-dom';
import JavascriptTimeAgo from 'javascript-time-ago';
import en from 'javascript-time-ago/locale/en';
import App from './App';

JavascriptTimeAgo.addLocale(en);

render(<App />, document.getElementById('root'));
