import { useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, useScroll, useTransform, useInView } from 'framer-motion'; 
import img from '../../assets/tailscale.jpeg';

import useMediaQuery from '../../hooks/useMediaQuery';

import styles from './downloadbox.module.css';

const imageVariants = {
    hidden: { opacity: 0 },
    visible: { 
        opacity: 1,
        transition: { duration: 0.8, delay: 0.3, ease: 'easeOut' }
    }
};

const coverVariants = {
    hidden: { x: 0 },
    visible: { 
        x: '100%',
        transition: { duration: 0.8, ease: 'easeInOut' }
    }
};


const Downloadbox = ({ headline, text }) => {
    const parallaxRef = useRef(null);
    const { scrollYProgress } = useScroll({
        target: parallaxRef,
        offset: ['start end', 'end start']
    });
    
    const isDesktop = useMediaQuery('(min-width: 1090px)');
    const range = isDesktop ? ['-25%', '30%'] : ['25%', '-10%'];

    const y = useTransform(scrollYProgress, [0, 1], range);

    const animationRef = useRef(null);
    const isInView = useInView(animationRef, { once: true, amount: 0.4 });

    return (
        <div ref={parallaxRef} className={styles.wrapper}>
            <motion.div 
                ref={animationRef} 
                style={{ y }}
                className={styles.sectionWrapper}
                initial="hidden"
                animate={isInView ? "visible" : "hidden"}
            >
                <div className={styles.shadowContainer}>
                    <div className={styles.imgRevealWrapper}>
                        <motion.img
                            className={styles.Img}
                            src={img}
                            alt='tailscale'
                            variants={imageVariants}
                        />
                        <motion.div 
                            className={styles.revealCover}
                            variants={coverVariants}
                        />
                    </div>
                </div>

                <div className={styles.contentWrapper}>
                    <h3>{headline}</h3>
                    <p>{text}</p>
                    <div className={styles.buttonContainer}>
                        <a 
                            href="https://tailscale.com/"
                            target="_blank" 
                            rel="noopener noreferrer"
                            className={styles.button}
                        >
                            Zur Tailscale Seite
                        </a>
                        <a 
                            href="mailto:OSDP@outlook.de?subject=Anfrage zur OSDP"
                            className={styles.button}
                        >
                            Kontakt per E-Mail
                        </a>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default Downloadbox;