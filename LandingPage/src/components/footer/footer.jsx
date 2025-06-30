// eslint-disable-next-line no-unused-vars
import { motion } from "framer-motion";
import styles from "./footer.module.css";
import { FaGithub, FaLinkedin, FaYoutube } from "react-icons/fa";

const socialLinks = [
  { href: "https://github.com/OSDP-Team", icon: <FaGithub size={70} />},
  { href: "https://www.linkedin.com/company/m&m-software-gmbh/", icon: <FaLinkedin size={70} /> },
  { href: "https://www.youtube.com/user/mmsoftwaregmbh", icon: <FaYoutube size={70} /> },
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

const Footer = () => {
  return (
    <div className={styles.wrapper}>
      <h2 className={styles.sectionHeadline}>Nützliche Links</h2>
      <motion.div
        className={styles.linkWrapper}
        variants={containerVariants}
        initial="hidden"
        whileInView="visible" 
        viewport={{ once: true, amount: 0.5 }}
      >
        {socialLinks.map((link, index) => (
          <motion.a
            key={index}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.button}
            variants={itemVariants} 
          >
            {link.icon}
          </motion.a>
        ))}
      </motion.div>
      <div className={styles.impressumWrapper}>
        <h2 className={styles.sectionHeadline}>Impressum</h2>
        <div className={styles.text}>
            <h4>Allgemine Informationen</h4>
            <p>
            M&M Software GmbH <br />
            Industriestr. 5 <br />
            78112 St. Georgen <br />
            GERMANY <br />
            <br />
            <b>Geschäftsführer:</b> <br />
            <br />
            Christian Gnädig, Thomas Gaus <br />
            <br />
            <b>Kontakt:</b> <br />
            <br />
            Phone +49 7724/9415-0 <br />
            Mail info@mm-software.com <br />
            <br />
            Registergericht: Amtsgericht Freiburg, HRB 602021 <br />
            <br />
            Umsatzsteuer-Identifikationsnummer: DE141908110 <br />
            <br />
            <br />
            </p>
            <h4>Haftungsausschlüsse</h4>
            <p>
            <b>1. Inhalt des Onlineangebots</b> <br />
            <br />
            M&M Software GmbH übernimmt keinerlei Gewähr für die Aktualität,
            Vollständigkeit, oder Qualität der bereit gestellten Informationen.
            Schadenersatzansprüche, bedingt durch die Nutzung dieser
            Informationen, sind grundsätzlich ausgeschlossen, sofern seitens M&M
            Software GmbH nicht nachweislich vorsätzliches oder grob
            fahrlässiges Verschulden vorliegt. <br />
            <br />
            <b>2. Verweise auf Links</b> <br />
            <br />
            Bei direkten oder indirekten Verweisen auf fremde Webseiten, die
            außerhalb des Verantwortungsbereichs von M&M Software GmbH liegen,
            haftet M&M Software GmbH lediglich, wenn sie von den Inhalten
            Kenntnis hat und es ihr technisch möglich und zumutbar ist, die
            Nutzung im Falle rechtwidriger Inhalte zu verhindern. M&M Software
            GmbH distanziert sich hiermit ausdrücklich von allen Inhalten
            verlinkter Seiten, Gästebüchern, Diskussionsforen etc., die
            rechtswidrig sind. Sämtliche Verstöße gegen geltendes Recht, die M&M
            Software GmbH bekannt werden, haben sofort eine Löschung der Links
            und sonstigen Eintragungen zur Folge. Für Schäden, die aus solchen
            Informationen entstehen, haftet allein der Autor der Seite bzw. der
            Autor der Fremdeinträge, auf welche auf der Web Seite von M&M
            Software GmbH verwiesen wurde, nicht M&M Software GmbH. <br />
            <br />
            <b>3. Copyright</b> <br />
            <br />
            Das Copyright am Inhalt dieser Webseite steht ausschließlich der M&M
            Software GmbH zu: Jedes Vervielfältigen und jede weitere Verwendung
            in andere Veröffentlichungen bedarf der Zustimmung der M&M Software
            GmbH.
            </p>
        </div>
      </div>
      <div className={styles.datenschutzWrapper}>
        <h2 className={styles.sectionHeadline}>Datenschutz</h2>
        <p>
          Diese Seite verwendet keine Cookies und speichert keine
          personenbezogenen Daten.
        </p>
      </div>
    </div>
  );
};

export default Footer;