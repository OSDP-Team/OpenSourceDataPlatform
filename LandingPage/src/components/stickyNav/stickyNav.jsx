import { useState, useEffect } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, AnimatePresence } from 'framer-motion';
import styles from './stickyNav.module.css';

const menuVariants = {
    closed: { x: '-100%', transition: { duration: 0.4, ease: 'easeInOut' } },
    open: { x: '0%', transition: { duration: 0.4, ease: 'easeInOut' } }
};

const overlayVariants = {
    closed: { opacity: 0 },
    open: { opacity: 1, transition: { duration: 0.3 } }
};

const linkContainerVariants = {
    closed: { opacity: 0 },
    open: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.3 } }
};

const linkItemVariants = {
    closed: { y: 20, opacity: 0 },
    open: { y: 0, opacity: 1 }
};

const StickyNav = ({ sections }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [activeSection, setActiveSection] = useState('intro');

    const scrollToSection = (id) => {
        setIsOpen(false);
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setActiveSection(entry.target.id);
                    }
                });
            },
            { rootMargin: '-50% 0px -50% 0px', threshold: 0 }
        );

        sections.forEach(section => {
            const element = document.getElementById(section.id);
            if (element) {
                observer.observe(element);
            }
        });

        return () => observer.disconnect();
    }, [sections]);

    const activeTitle = sections.find(s => s.id === activeSection)?.title || 'Menü';

    return (
        <>
            <button className={styles.stickyTrigger} onClick={() => setIsOpen(true)}>
                <div className={styles.verticalText}>{activeTitle}</div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            className={styles.closeOverlay}
                            onClick={() => setIsOpen(false)}
                            variants={overlayVariants}
                            initial="closed"
                            animate="open"
                            exit="closed"
                        />
                        
                        <motion.nav
                            className={styles.menuContainer}
                            variants={menuVariants}
                            initial="closed"
                            animate="open"
                            exit="closed"
                        >
                            <motion.ul
                                className={styles.linkList}
                                variants={linkContainerVariants}
                            >
                                {sections.map(section => (
                                    <motion.li key={section.id} variants={linkItemVariants}>
                                        <button onClick={() => scrollToSection(section.id)}>
                                            <span>{section.title}</span>
                                        </button>
                                    </motion.li>
                                ))}
                            </motion.ul>
                        </motion.nav>
                    </>
                )}
            </AnimatePresence>
        </>
    );
};

export default StickyNav;