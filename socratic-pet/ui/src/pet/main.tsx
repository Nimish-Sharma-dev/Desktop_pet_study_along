import React from 'react';
import ReactDOM from 'react-dom/client';
import '../styles/index.css';
import { startUiFeed } from '../api/feed';
import { ArtGallery } from './ArtGallery';
import { PetApp } from './PetApp';

const gallery = new URLSearchParams(window.location.search).has('gallery');
if (!gallery) startUiFeed();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>{gallery ? <ArtGallery /> : <PetApp />}</React.StrictMode>,
);
