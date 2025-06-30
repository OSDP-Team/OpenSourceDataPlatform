// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import ServiceCard from './serviceCard/serviceCard';
import styles from './service.module.css';

import jupyter from '../../assets/jupyter.png'; 
import minio from '../../assets/minio.webp'; 
import keycloak from '../../assets/keycloak.png'; 
import superset from '../../assets/apache-superset.webp'; 
import airflow from '../../assets/airflow.png'; 


const servicesData = [
    { img: jupyter, headline: "Jupyterhub", text: "Die Entwicklungsumgebung auf der Cloud mit Versionierung über GitHub.", path: "https://httpd.apache.org" },
    { img: minio, headline: "MinIO", text: "Speicherort für Roh- und verarbeiteter Daten. Zielort der Medaillon-Architektur.", path: "https://httpd.apache.org" },
    { img: keycloak, headline: "Keycloak", text: "Zentrales Authentifizierungstool, zur Verwaltung von Zugangsdaten.", path: "https://httpd.apache.org" },
    { img: superset, headline: "Superset", text: "BI-Tool zur Visualisierung der verarbeiteten Daten in Form von Dashboards.", path: "https://httpd.apache.org" },
    { img: airflow, headline: "Airflow", text: "Orchestrierungstool für die gesamten Workflows der Platform.", path: "https://httpd.apache.org" },
];

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.2 
        }
    }
};

const itemVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: {
        scale: 1,
        opacity: 1,
        transition: {
            duration: 0.5
        }
    }
};


const Service = () => {
    return (
        <section className={styles.wrapper}>
            <h2 className={styles.sectionHeadline}>Unsere Services</h2>
            <motion.div
                className={styles.cardContainer}
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, amount: 0.2 }}
            >
                {servicesData.map((service, index) => (
                    <motion.div 
                        key={index} 
                        variants={itemVariants} 
                        className={styles.cardWrapper}
                    >
                        <ServiceCard
                            img={service.img}
                            headline={service.headline}
                            text={service.text}
                            path={service.path}
                        />
                    </motion.div>
                ))}
            </motion.div>
        </section>
    );
};

export default Service;