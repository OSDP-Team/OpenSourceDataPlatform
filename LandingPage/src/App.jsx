import { useEffect } from 'react';
import Lenis from '@studio-freight/lenis';

import styles from './App.module.css';

import StickyNav from './components/stickyNav/stickyNav';
import ScrollButton from './components/scrollButton/scrollButton'

import Header from './components/header/header';
import Team from './components/team/team';
import Intro from './components/intro/intro'
import Downloadbox from './components/Downloadbox/downloadbox';
import Service from './components/service/service';
import Footer from './components/Footer/footer';

const sectionsForNav = [
  { id: 'einfuehrung', title: 'Einführung' },
  { id: 'team', title: 'Team' },
  { id: 'voraussetzungen', title: 'Voraussetzungen' },
  { id: 'services', title: 'Services' },
  { id: 'nuetzliches', title: 'Nützliches' },
];

function App() {
  useEffect(() => {
    const lenis = new Lenis();

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);
    
    return () => {
      lenis.destroy();
    };
  }, []);

  return (
    <div>
      <StickyNav 
        sections={sectionsForNav}
      />

      <Header
        headline="Open-Source-Data-Platform"
        subheadline="Willkommen zur Übersichtsseite der OSDP"
      />

      <section id='einfuehrung'>
        <h2 className={styles.sectionHeadline}>Einführung</h2>
        <Intro
          headline="Das OSDP-Projekt"
          text="Die Open-Source-Data-Platform (kurz OSDP), soll es ermöglichen Heizkraftwerk Daten zu speichern, zu verarbeiten und auszuwerten. Diese Seite soll dabei einen Überblick darüber schaffen, wer hinter dem Projekt steht, was die OSDP alles kann und hauptsächlich die Verwendung der Plattform vereinfachen."
        />
      </section>

      <section id='team'>
        <Team />
      </section>

      <section id='voraussetzungen'>
        <h2 className={styles.sectionHeadline}>Bevor du startest...</h2>
        <Downloadbox
          headline="Tailscale-VPN"
          text="Damit die Platform sicher bleibt, müssen sie zuvor Tailscale einrichten, um die OSDP Anwendung zu verwenden. Für die genaue Konfiguration melden sie sich gerne bei einem der Teammitglieder oder schauen Sie sich die Dokumentation an!"
        />
      </section>

      <section id='services'>
        <Service />
      </section>

      <section id='nuetzliches'>
        <Footer />  
      </section>

      <ScrollButton />
    </div>
  )
}

export default App
