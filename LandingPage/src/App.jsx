import { useEffect } from 'react';
import Lenis from '@studio-freight/lenis';

import styles from './App.module.css';

import StickyNav from './components/stickyNav/stickyNav';
import ScrollButton from './components/scrollButton/scrollButton'

import Header from './components/header/header';
import Team from './components/team/team';
import Intro from './components/intro/intro'
import Downloadbox from './components/downloadbox/downloadbox';
import Service from './components/service/service';
import Footer from './components/footer/footer';
import Separator from './components/separator/separator';

import dummy from './assets/dummy.png'

import jupyter from './assets/jupyter.png'; 
import minio from './assets/minio.webp'; 
import keycloak from './assets/keycloak.png'; 
import superset from './assets/apache-superset.webp'; 
import airflow from './assets/airflow.png'; 

import azure from './assets/azure.png'; 
import kubernetes from './assets/kubernetes.png'; 

const osServices = [
    { img: jupyter, headline: "Jupyterhub", text: "Die Entwicklungsumgebung auf der Cloud mit Versionierung über GitHub.", path: "10.0.194.12" },
    { img: minio, headline: "MinIO", text: "Speicherort für Roh- und verarbeiteter Daten. Zielort der Medaillon-Architektur.", path: "https://httpd.apache.org" },
    { img: keycloak, headline: "Keycloak", text: "Zentrales Authentifizierungstool, zur Verwaltung von Zugangsdaten.", path: " https://10.0.234.7:8443/" },
    { img: superset, headline: "Superset", text: "BI-Tool zur Visualisierung der verarbeiteten Daten in Form von Dashboards.", path: "http://10.0.176.231:8088/" },
    { img: airflow, headline: "Airflow", text: "Orchestrierungstool für die gesamten Workflows der Platform.", path: "https://httpd.apache.org" },
];

const infrastructure = [
    { img: azure, headline: "Azure", text: "Die Cloud-Infrastruktur auf der die Datenplattform läuft.", path: "https://httpd.apache.org" },
    { img: kubernetes, headline: "Kubernetes", text: "Open-Source System zur Verwaltung von Container Anwendungen.", path: "https://httpd.apache.org" }
];

const sectionsForNav = [
  { id: 'einfuehrung', title: 'Einführung' },
  { id: 'team', title: 'Team' },
  { id: 'voraussetzungen', title: 'Voraussetzungen' },
  { id: 'infrastruktur', title: 'Infrastruktur' },
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

      <section id='infrastruktur'>
        <Service
          servicesData={infrastructure}
          sectionTitle="Unsere Infrastruktur"
        />
      </section>

      <Separator imageUrl={dummy} />

      <section id='services'>
        <Service
          servicesData={osServices}
          sectionTitle="Unsere Services"
        />
      </section>

      <section id='nuetzliches'>
        <Footer />  
      </section>

      <ScrollButton />
    </div>
  )
}

export default App
