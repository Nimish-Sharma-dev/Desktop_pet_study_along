import React from 'react';
import ReactDOM from 'react-dom/client';
import '../styles/index.css';
import { startUiFeed } from '../api/feed';
import { DashboardApp } from './DashboardApp';

startUiFeed();
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><DashboardApp /></React.StrictMode>);
